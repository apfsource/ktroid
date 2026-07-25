
import os
import sys
import shutil
import subprocess
import urllib.request
import zipfile
import ssl
import typer
from rich.prompt import Confirm
from ktroid.core.utils import print_info, print_success, print_error, print_warning, run_command, get_script_dir
from ktroid.core.config import CONFIG

CMD_TOOLS_URL = "https://dl.google.com/android/repository/commandlinetools-linux-14742923_latest.zip"
GRADLE_dist_URL = "https://services.gradle.org/distributions/gradle-9.3.1-bin.zip"

def check_env():
    """Verify the environment requirements."""
    print_info("Checking environment...")
    
    # Check JDK
    try:
        result = subprocess.run(['java', '-version'], capture_output=True, text=True)
        version_output = result.stderr
        if "version" in version_output:
            print_success(f"[OK] Java found: {version_output.splitlines()[0]}")
            req_java = CONFIG['java_version']
            if req_java not in version_output and f"1.{req_java}" not in version_output:
                 print_warning(f"[WARN] Java {req_java} is recommended. Found version might differ.")
        else:
            print_error("[ERR] Java not found or version output parse error.")
    except FileNotFoundError:
        print_error("[ERR] Java not found in PATH.")

    # Check ANDROID_HOME
    android_home = os.environ.get('ANDROID_HOME')
    if android_home:
         print_success(f"[OK] ANDROID_HOME set to: {android_home}")
         # Check platforms
         platforms_dir = os.path.join(android_home, 'platforms')
         if os.path.exists(platforms_dir):
             platforms = os.listdir(platforms_dir)
             print_success(f"[OK] Android platforms found: {', '.join(platforms)}")
         else:
             print_error("[ERR] $ANDROID_HOME/platforms directory not found.")
    else:
        print_error("[ERR] ANDROID_HOME environment variable is NOT set.")

    # Check ADB
    if shutil.which("adb"):
        print_success("[OK] adb found.")
    elif android_home and os.path.exists(os.path.join(android_home, "platform-tools", "adb")):
        print_success(f"[OK] adb found in platform-tools (not in PATH).")
    else:
        print_error("[ERR] adb not found.")

    # Check Gradle (System)
    if shutil.which("gradle"):
        print_success("[OK] System Gradle found (can be used to bootstrap wrapper).")
    else:
        print_warning("[WARN] System Gradle not found. 'ktroid create' requires gradle to generate the wrapper.")

    # Check current directory wrapper
    if os.path.exists("gradlew"):
        print_success("[OK] Local Gradle wrapper (gradlew) found in current directory.")



def download_progress_hook(count, block_size, total_size):
    """Simple progress bar hook."""
    global start_time
    if count == 0:
        start_time = time.time()
        return
        
    duration = time.time() - start_time
    progress_size = int(count * block_size)
    percent = int(count * block_size * 100 / total_size)
    
    # Simple bar: [===========>        ]
    bar_len = 30
    filled_len = int(bar_len * percent / 100)
    bar = '=' * filled_len + '>' + ' ' * (bar_len - filled_len - 1)
    
    # MB conversion
    size_mb = total_size / (1024 * 1024)
    prog_mb = progress_size / (1024 * 1024)
    
    sys.stdout.write(f"\rDownloading: {prog_mb:.1f} MB / {size_mb:.1f} MB [{bar}] {percent}%")
    sys.stdout.flush()

import time # Need time for progress bar




from rich.progress import Progress, SpinnerColumn, DownloadColumn, TextColumn, BarColumn, TimeRemainingColumn
import urllib.request
import zipfile
import stat
import platform
import subprocess

def setup():
    """Master Setup Wizard for Android Environment."""
    from rich.prompt import Prompt, Confirm
    
    print_info("=== ktd Master Setup Wizard ===")
    
    # --- 1. JDK Check & Advice ---
    print_info("\n[1/4] Checking Java Development Kit (JDK)...")
    import shutil
    if shutil.which("java"):
        try:
            result = subprocess.run(['java', '-version'], capture_output=True, text=True)
            if result.returncode == 0:
                print_success(f"[OK] Java is installed: {result.stderr.splitlines()[0]}")
            else:
                print_warning(f"[WARN] Java executable found, but execution failed: {result.stderr.strip()}")
        except Exception as e:
            print_warning(f"[WARN] Java executable found, but an error occurred checking version: {e}")
    else:
        print_error("[MISSING] Java JDK was not found on your system.")
        print_warning("Java is a system-level dependency required by Gradle and Android SDK.")
        print_info("Please install it manually based on your OS:")
        print(" - Linux:   sudo apt install openjdk-17-jdk")
        print(" - Mac:     brew install openjdk@17")
        print(" - Windows: Download from https://adoptium.net/temurin/releases/")
        if not Confirm.ask("Do you want to continue setup without Java for now?", default=False):
            return

    # --- 2. Custom Path Selection ---
    print_info("\n[2/4] Setup Location")
    default_dest = os.path.expanduser("~/android") if os.name != 'nt' else "C:\\Android"
    dest_root = Prompt.ask("Enter installation path", default=default_dest)
    dest_root = os.path.expanduser(dest_root)
    os.makedirs(dest_root, exist_ok=True)
    print_success(f"Using directory: {dest_root}")

    # --- 3. Downloads (Gradle & Cmdline Tools) ---
    print_info("\n[3/4] Downloading Core Tools")
    
    gradle_version = CONFIG.get("gradle_version", "9.3.1")
    gradle_url = f"https://services.gradle.org/distributions/gradle-{gradle_version}-bin.zip"
    
    os_name = platform.system().lower()
    if 'linux' in os_name:
        cmd_tools_url = "https://dl.google.com/android/repository/commandlinetools-linux-14742923_latest.zip"
    elif 'darwin' in os_name:
        cmd_tools_url = "https://dl.google.com/android/repository/commandlinetools-mac-14742923_latest.zip"
    else:
        cmd_tools_url = "https://dl.google.com/android/repository/commandlinetools-win-14742923_latest.zip"

    def download_and_extract(url, name, dest_extract):
        filename = url.split('/')[-1]
        filepath = os.path.join(dest_root, filename)
        
        if not os.path.exists(filepath):
            try:
                with Progress(
                    SpinnerColumn(),
                    TextColumn(f"[bold blue]Downloading {name}..."),
                    BarColumn(),
                    DownloadColumn(),
                    TimeRemainingColumn(),
                ) as progress:
                    task = progress.add_task("Download", total=None)
                    
                    def report_hook(count, block_size, total_size):
                        if progress.tasks[task].total is None:
                            progress.update(task, total=total_size)
                        progress.update(task, completed=count * block_size)
                        
                    urllib.request.urlretrieve(url, filepath, reporthook=report_hook)
                print_success(f"Successfully downloaded {name}")
            except Exception as e:
                print_error(f"Failed to download {name}: {e}")
                return False
        else:
            print_success(f"File {filename} already exists, skipping download.")

        print_info(f"Extracting {name}...")
        try:
            with zipfile.ZipFile(filepath, 'r') as zip_ref:
                zip_ref.extractall(dest_extract)
            print_success(f"Extracted {name}")
            return True
        except Exception as e:
            print_error(f"Failed to extract {name}: {e}")
            return False

    # Download Gradle
    if Confirm.ask(f"Download and setup Gradle {gradle_version}?", default=True):
        download_and_extract(gradle_url, "Gradle", dest_root)
        
    # Download Cmdline tools
    cmd_tools_extracted = False
    if Confirm.ask("Download and setup Android Command Line Tools?", default=True):
        temp_cmd_dir = os.path.join(dest_root, "cmdline-temp")
        cmd_tools_extracted = download_and_extract(cmd_tools_url, "Android Cmdline Tools", temp_cmd_dir)
        
        # Fix directory structure for sdkmanager
        if cmd_tools_extracted:
            final_cmd_dir = os.path.join(dest_root, "cmdline-tools", "latest")
            os.makedirs(os.path.dirname(final_cmd_dir), exist_ok=True)
            source_cmd = os.path.join(temp_cmd_dir, "cmdline-tools")
            if os.path.exists(source_cmd) and not os.path.exists(final_cmd_dir):
                os.rename(source_cmd, final_cmd_dir)
            shutil.rmtree(temp_cmd_dir, ignore_errors=True)

    # --- 4. Android SDK Manager Automation ---
    print_info("\n[4/4] Android SDK Packages")
    
    sdkmanager_name = "sdkmanager.bat" if os.name == 'nt' else "sdkmanager"
    sdkmanager_path = os.path.join(dest_root, "cmdline-tools", "latest", "bin", sdkmanager_name)
    
    if os.path.exists(sdkmanager_path):
        if os.name != 'nt':
            st = os.stat(sdkmanager_path)
            os.chmod(sdkmanager_path, st.st_mode | stat.S_IEXEC)
            
        print_info("Android SDK Mapping:")
        print(" 35 = Android 15\n 34 = Android 14\n 33 = Android 13")
        sdks_input = Prompt.ask("Enter required SDK versions (comma-separated)", default=str(CONFIG.get("compile_sdk", "35")))
        sdks = [s.strip() for s in sdks_input.split(',')]
        
        packages_to_install = ["platform-tools"]
        for sdk in sdks:
            packages_to_install.append(f"platforms;android-{sdk}")
            packages_to_install.append(f"build-tools;{sdk}.0.0")
            
        print_info(f"The following packages will be installed: {', '.join(packages_to_install)}")
        if Confirm.ask("Do you want to install them now using sdkmanager?", default=True):
            print_info("Accepting licenses and downloading packages... This may take a while.")
            try:
                yes_cmd = "echo y" if os.name == 'nt' else "yes"
                license_cmd = f"{yes_cmd} | \"{sdkmanager_path}\" --licenses"
                subprocess.run(license_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                install_cmd = [sdkmanager_path] + packages_to_install
                subprocess.run(install_cmd, check=True)
                print_success("Android SDK packages installed successfully!")
            except Exception as e:
                print_error(f"Failed to install SDK packages: {e}")
    else:
        print_warning("sdkmanager not found. Skipping SDK package installation.")

    # --- 5. Export Variables ---
    print_info("\n=== Setup Summary & Environment Variables ===")
    
    bashrc_path = os.path.expanduser("~/.bashrc")
    zshrc_path = os.path.expanduser("~/.zshrc")
    
    g_dirs = [d for d in os.listdir(dest_root) if d.startswith("gradle-")] if os.path.exists(dest_root) else []
    
    if os.name != 'nt':
        exports = [
            f'export ANDROID_HOME="{dest_root}"',
            f'export PATH="$PATH:{os.path.join(dest_root, "cmdline-tools", "latest", "bin")}"',
            f'export PATH="$PATH:{os.path.join(dest_root, "platform-tools")}"'
        ]
        if g_dirs:
            g_bin = os.path.join(dest_root, sorted(g_dirs)[-1], "bin")
            exports.append(f'export PATH="$PATH:{g_bin}"')
            
        print_info("The following paths need to be added to your system:")
        for exp in exports:
            print(f"  [cyan]{exp}[/cyan]")
            
        print_warning("\nYou can add these manually, or I can do it for you.")
        if Confirm.ask("Do you want me to automatically append these to your ~/.bashrc (or ~/.zshrc)?", default=True):
            target_rc = zshrc_path if os.path.exists(zshrc_path) else bashrc_path
            try:
                with open(target_rc, "a") as f:
                    f.write("\n# Added by ktd setup\n")
                    for exp in exports:
                        f.write(exp + "\n")
                print_success(f"Added to {target_rc}. Please run 'source {target_rc}' to apply.")
            except Exception as e:
                print_error(f"Failed to write to {target_rc}: {e}")
        else:
            print_info("Skipped auto-path setup. Please add them manually.")
            
    else:
        # Windows Path Setup
        print_info("The following paths need to be added to your Windows Environment Variables:")
        print(f"  [cyan]ANDROID_HOME = {dest_root}[/cyan]")
        print(f"  [cyan]PATH += {os.path.join(dest_root, 'cmdline-tools', 'latest', 'bin')}[/cyan]")
        print(f"  [cyan]PATH += {os.path.join(dest_root, 'platform-tools')}[/cyan]")
        if g_dirs:
            print(f"  [cyan]PATH += {os.path.join(dest_root, sorted(g_dirs)[-1], 'bin')}[/cyan]")
            
        print_warning("\nYou can add these manually in System Properties, or I can do it for you (Current User only).")
        if Confirm.ask("Do you want me to automatically add these to your Windows Registry?", default=True):
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS)
                winreg.SetValueEx(key, "ANDROID_HOME", 0, winreg.REG_SZ, dest_root)
                
                try:
                    path_val, _ = winreg.QueryValueEx(key, "PATH")
                except FileNotFoundError:
                    path_val = ""
                    
                new_paths = [
                    os.path.join(dest_root, "cmdline-tools", "latest", "bin"),
                    os.path.join(dest_root, "platform-tools")
                ]
                if g_dirs:
                    new_paths.append(os.path.join(dest_root, sorted(g_dirs)[-1], "bin"))
                    
                for np in new_paths:
                    if np not in path_val:
                        path_val = path_val + ";" + np if path_val else np
                        
                winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, path_val)
                winreg.CloseKey(key)
                
                print_success("Successfully added to Windows Registry!")
                print_warning("Note: You must completely restart your terminal (or PC) for Windows to load the new PATH.")
            except ImportError:
                print_error("winreg module not found. Please add paths manually.")
            except Exception as e:
                print_error(f"Failed to add to Windows Registry: {e}. Please add manually or run terminal as Administrator.")
        else:
            print_info("Skipped auto-path setup. Please add them manually.")

def check():
    """Check dependencies"""
    check_env()

def config():
    """Show current configuration"""
    from ktroid.core.utils import print_info
    import json
    print_info("Current Configuration:")
    print(json.dumps(CONFIG, indent=4))

import urllib.request
import json
import re
from rich.prompt import Prompt

def fetch_latest_gradle():
    try:
        req = urllib.request.Request("https://services.gradle.org/versions/all", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            stable = [v["version"] for v in data if not v.get("snapshot") and not v.get("rc") and not v.get("milestone") and not v.get("nightly")]
            return stable[0], stable[1:6]
    except:
        return None, []

def fetch_latest_kotlin():
    try:
        req = urllib.request.Request("https://api.github.com/repos/JetBrains/kotlin/releases", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            stable = [v["tag_name"].replace("v", "") for v in data if not v.get("prerelease") and "RC" not in v["tag_name"] and "Beta" not in v["tag_name"]]
            return stable[0], stable[1:6]
    except:
        return None, []

def fetch_latest_agp():
    try:
        req = urllib.request.Request("https://dl.google.com/dl/android/maven2/com/android/tools/build/gradle/maven-metadata.xml", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            xml = response.read().decode()
            versions = re.findall(r'<version>(.*?)</version>', xml)
            stable = [v for v in versions if '-' not in v and v.count('.') >= 2]
            return stable[-1], list(reversed(stable[-6:-1]))
    except:
        return None, []


def verify_gradle(v):
    import urllib.request
    try:
        req = urllib.request.Request(f"https://services.gradle.org/distributions/gradle-{v}-bin.zip", method="HEAD", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status == 200
    except:
        return False

def verify_kotlin(v):
    import urllib.request
    try:
        req = urllib.request.Request(f"https://api.github.com/repos/JetBrains/kotlin/releases/tags/v{v}", method="HEAD", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status == 200
    except:
        return False

def verify_agp(v):
    import urllib.request
    try:
        url = f"https://dl.google.com/dl/android/maven2/com/android/tools/build/gradle/{v}/gradle-{v}.pom"
        req = urllib.request.Request(url, method="HEAD", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status == 200
    except:
        return False

def update_config():
    """Interactive Configuration Updater"""
    from ktroid.core.config import CONFIG, save_config
    
    print_info("Fetching latest versions from the internet... Please wait.")
    
    latest_gradle, recent_gradle = fetch_latest_gradle()
    latest_kotlin, recent_kotlin = fetch_latest_kotlin()
    latest_agp, recent_agp = fetch_latest_agp()
    
    updates = {}
    
    def prompt_version(key, display_name, latest_ver, recent_vers, verify_func=None):
        current_ver = CONFIG.get(key)
        print("\n" + "-"*40)
        print_info(f"Configuring {display_name}")
        print(f"Current Default: {current_ver}")
        if latest_ver:
            print(f"Latest Stable:   {latest_ver}")
            print(f"Recent Versions: {', '.join(recent_vers)}")
        else:
            print("Latest Stable:   [Failed to fetch]")
            
        choices = ["Default", "Latest", "Custom"]
        choice = Prompt.ask(f"Select option for {display_name}", choices=choices, default="Default")
        
        if choice == "Latest" and latest_ver:
            return latest_ver
        elif choice == "Custom":
            while True:
                custom_ver = Prompt.ask("Enter custom version")
                if not verify_func:
                    return custom_ver
                
                print(f"Verifying {custom_ver}...")
                if verify_func(custom_ver):
                    print_success(f"Version {custom_ver} verified successfully! [OK]")
                    return custom_ver
                else:
                    print_error(f"Version '{custom_ver}' could not be found on official servers. Are you sure it's correct?")
                    retry = Prompt.ask("Do you want to try another version?", choices=["y", "n"], default="y")
                    if retry == "n":
                        print("Falling back to Default.")
                        return current_ver
        else:
            return current_ver
            
    updates["gradle_version"] = prompt_version("gradle_version", "Gradle", latest_gradle, recent_gradle, verify_gradle)
    updates["kotlin_version"] = prompt_version("kotlin_version", "Kotlin", latest_kotlin, recent_kotlin, verify_kotlin)
    updates["agp_version"] = prompt_version("agp_version", "Android Gradle Plugin (AGP)", latest_agp, recent_agp, verify_agp)
    
    # Prompt for other basic configs without latest checks
    updates["compile_sdk"] = Prompt.ask("\nCompile SDK", default=CONFIG.get("compile_sdk"))
    updates["min_sdk"] = Prompt.ask("Min SDK", default=CONFIG.get("min_sdk"))
    updates["target_sdk"] = Prompt.ask("Target SDK", default=CONFIG.get("target_sdk"))
    updates["java_version"] = Prompt.ask("Java Version", default=CONFIG.get("java_version"))
    
    print("\n" + "-"*40)
    print_info("Saving new configuration...")
    if save_config(updates):
        print_success("Configuration updated successfully!")
    else:
        print_error("Failed to update configuration.")
