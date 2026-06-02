
import os
import sys
import re
import subprocess
import typer
from rich.prompt import Confirm
from ktroid.core.utils import print_info, print_success, print_error, print_warning, run_command

def get_connected_devices():
    """Return list of connected devices."""
    try:
        res = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        lines = res.stdout.splitlines()
        devices = []
        for line in lines[1:]: # Skip header
             parts = line.split()
             if len(parts) >= 2 and parts[1] == "device":
                 devices.append(parts[0])
        return devices
    except:
        return []



def logs():
    """Smart Logcat Viewer."""
    # 1. Get Package Name (from build.gradle or user input?)
    # Parsing build.gradle for applicationId
    app_id = None
    if os.path.exists("app/build.gradle"):
         with open("app/build.gradle", "r") as f:
             cnt = f.read()
             m = re.search(r'applicationId\s+"?([^"\n]+)"?', cnt)
             if m: app_id = m.group(1)
    
    if not app_id:
        print_error("Could not find applicationId in app/build.gradle.")
        return
        
    print_info(f"Filtering logs for: {app_id}")
    
    # Get PID for app
    try:
        pid_res = subprocess.run(f"adb shell pidof {app_id}", shell=True, capture_output=True, text=True)
        pid = pid_res.stdout.strip()
        if not pid:
            print_warning("App is not running. Showing all logs containing package name...")
            filter_cmd = app_id
        else:
            print_info(f"PID found: {pid}")
            filter_cmd = f" --pid={pid}"
            
        # Run logcat
        # Simple colorizer logic is hard in python subprocess pipe loop
        # We'll just run adb logcat and let grep handle it or raw
        print_success("Ctrl+C to stop.")
        
        # Color command for grep if possible or just raw
        # Using grep to filter is better
        cmd = f"adb logcat -v time | grep '{app_id}'" if not pid else f"adb logcat -v time --pid={pid}"
        
        # Run
        os.system(cmd)
        
    except KeyboardInterrupt:
        print()
    except Exception as e:
        print_error(f"Logcat error: {e}")



def emulator(action: str = typer.Argument(..., help="Action (list, start, create)"),
             name: str = typer.Argument(None, help="Name of the emulator to start")):
    """Manage Android Emulators."""
    
    if action == "list":
        # List all AVDs
        print_info("Available AVDs:")
        try:
            result = subprocess.run(["emulator", "-list-avds"], capture_output=True, text=True)
            if result.stdout.strip():
                avds = result.stdout.strip().split('\n')
                for i, avd in enumerate(avds, 1):
                    print(f"  {i}. {avd}")
            else:
                print_warning("No AVDs found. Create one using: ktroid emulator create")
        except FileNotFoundError:
            print_error("'emulator' command not found. Ensure $ANDROID_HOME/emulator is in PATH.")
    
    elif action == "start":
        # Start an emulator
        if name:
            avd_name = name
        else:
            # List and select
            try:
                result = subprocess.run(["emulator", "-list-avds"], capture_output=True, text=True)
                avds = result.stdout.strip().split('\n') if result.stdout.strip() else []
                
                if not avds:
                    print_error("No AVDs found. Create one first.")
                    return
                
                print_info("Available AVDs:")
                for i, avd in enumerate(avds, 1):
                    print(f"  {i}. {avd}")
                
                try:
                    sel = int(typer.prompt("Select AVD (number): "))
                    avd_name = avds[sel - 1]
                except:
                    print_error("Invalid selection.")
                    return
            except FileNotFoundError:
                print_error("'emulator' command not found.")
                return
        
        print_info(f"Starting emulator: {avd_name}")
        print_warning("Emulator will run in background. Check with 'adb devices'.")
        
        # Start in background
        android_home = os.environ.get('ANDROID_HOME')
        if android_home:
            emulator_path = os.path.join(android_home, "emulator", "emulator")
            if os.path.exists(emulator_path):
                subprocess.Popen([emulator_path, "-avd", avd_name], 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL)
                print_success(f"Emulator '{avd_name}' started.")
            else:
                print_error("Emulator binary not found in $ANDROID_HOME/emulator/")
        else:
            # Try system emulator
            try:
                subprocess.Popen(["emulator", "-avd", avd_name], 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL)
                print_success(f"Emulator '{avd_name}' started.")
            except FileNotFoundError:
                print_error("'emulator' command not found.")
    
    elif action == "create":
        # Create new AVD (simplified)
        print_info("Creating new AVD...")
        
        avd_name = typer.prompt("AVD Name [Pixel_API_35]: ").strip() or "Pixel_API_35"
        device_type = typer.prompt("Device Type [pixel_7]: ").strip() or "pixel_7"
        system_image = typer.prompt("System Image [system-images;android-35;google_apis;x86_64]: ").strip() or "system-images;android-35;google_apis;x86_64"
        
        # Check if image is installed
        print_info(f"Checking if system image is installed...")
        try:
            result = subprocess.run(["sdkmanager", "--list_installed"], capture_output=True, text=True)
            if system_image not in result.stdout:
                print_warning(f"System image not installed: {system_image}")
                confirm = typer.prompt("Install now? (y/n): ")
                if confirm.lower() == 'y':
                    print_info("Installing system image...")
                    install_cmd = f"yes | sdkmanager '{system_image}'"
                    os.system(install_cmd)
                else:
                    print_warning("Cannot create AVD without system image.")
                    return
        except FileNotFoundError:
            print_error("'sdkmanager' not found. Cannot verify system image.")
            return
        
        # Create AVD
        print_info(f"Creating AVD '{avd_name}'...")
        cmd = f"echo no | avdmanager create avd -n {avd_name} -k '{system_image}' -d {device_type}"
        
        if run_command(cmd, show_output=True):
            print_success(f"AVD '{avd_name}' created successfully.")
            print_info(f"Start with: ktroid emulator start {avd_name}")
        else:
            print_error("Failed to create AVD.")
    
    else:
        print_error(f"Unknown emulator action: {action}")



def install(apk_path: str = typer.Argument(..., help="Path to APK file")):
    """Install an APK to device."""
    
    if not os.path.exists(apk_path):
        print_error(f"APK not found: {apk_path}")
        return
    
    # Get devices
    devices = get_connected_devices()
    if not devices:
        print_error("No connected devices found.")
        return
    
    target_device = devices[0]
    if len(devices) > 1:
        print_info("Multiple devices found:")
        for i, d in enumerate(devices):
            print(f"{i+1}. {d}")
        
        try:
            sel = int(typer.prompt("Select device (number): "))
            target_device = devices[sel-1]
        except:
            print_error("Invalid selection.")
            return
    
    print_info(f"Installing {os.path.basename(apk_path)} to {target_device}...")
    
    if run_command(f"adb -s {target_device} install -r {apk_path}"):
        print_success("APK installed successfully.")
    else:
        print_error("Installation failed.")



def uninstall(package_name: str = typer.Argument(None, help="Package name to uninstall")):
    """Uninstall app from device."""
    # Get package name
    package_name = package_name
    
    if not package_name:
        # Try to get from build.gradle
        if os.path.exists("app/build.gradle"):
            with open("app/build.gradle", "r") as f:
                cnt = f.read()
                m = re.search(r'applicationId\s+"?([^"\n]+)"?', cnt)
                if m:
                    package_name = m.group(1)
        
        if not package_name:
            print_error("Package name not found. Provide it with: ktroid uninstall <package>")
            return
    
    # Get devices
    devices = get_connected_devices()
    if not devices:
        print_error("No connected devices found.")
        return
    
    target_device = devices[0]
    if len(devices) > 1:
        print_info("Multiple devices found:")
        for i, d in enumerate(devices):
            print(f"{i+1}. {d}")
        
        try:
            sel = int(typer.prompt("Select device (number): "))
            target_device = devices[sel-1]
        except:
            print_error("Invalid selection.")
            return
    
    print_info(f"Uninstalling {package_name} from {target_device}...")
    
    if run_command(f"adb -s {target_device} uninstall {package_name}"):
        print_success("App uninstalled successfully.")
    else:
        print_error("Uninstallation failed.")


