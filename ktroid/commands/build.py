
import os
import sys
import shutil
import typer
import re
import subprocess
from rich.prompt import Confirm
from ktroid.core.utils import print_info, print_success, print_error, print_warning, run_command, get_script_dir, find_project_root
from ktroid.core.config import CONFIG
from ktroid.commands.device import get_connected_devices

def verify_apk(apk_path):
    """Verify APK signature using apksigner or jarsigner."""
    print_info(f"Verifying signature for: {os.path.basename(apk_path)}")
    
    # Try apksigner (Best)
    # Usually in $ANDROID_HOME/build-tools/<version>/apksigner
    apksigner = shutil.which("apksigner")
    if not apksigner and os.environ.get("ANDROID_HOME"):
         # Try to find it manually
         bt_dir = os.path.join(os.environ["ANDROID_HOME"], "build-tools")
         if os.path.exists(bt_dir):
             versions = sorted(os.listdir(bt_dir))
             if versions:
                 candidate = os.path.join(bt_dir, versions[-1], "apksigner")
                 if os.path.exists(candidate):
                     apksigner = candidate

    verified = False
    if apksigner:
        cmd = f"{apksigner} verify --verbose {apk_path}"
        # We need output
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print_success("[OK] APK Verified (apksigner).")
            verified = True
        else:
            print_error(f"[ERR] Verification failed: {result.stderr}")
    else:
        # Fallback to jarsigner
        print_info("apksigner not found. Falling back to jarsigner...")
        if shutil.which("jarsigner"):
             cmd = f"jarsigner -verify -verbose -certs {apk_path}"
             result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
             if "jar verified" in result.stdout:
                  print_success("[OK] APK Verified (jarsigner).")
                  verified = True
                  if "CN=Android Debug" in result.stdout:
                      print_warning("[WARN] Signed with DEBUG key.")
             else:
                 print_error("[ERR] Verification failed.")
        else:
             print_warning("[WARN] Neither apksigner nor jarsigner found. Cannot verify.")

    if not verified:
         print_error("WARNING: App is NOT signed properly.")



def build(action: str = typer.Argument("debug", help="Build type (debug, release, bundle)")):
    """Build the project"""
    project_root = find_project_root()
    if not project_root:
        print_error("Error: Project root not found. Are you inside an Android project?")
        sys.exit(1)
    os.chdir(project_root)

    if not os.path.exists("./gradlew"):
        print_error("Error: gradlew not found in project root.")
        sys.exit(1)

    # Ensure executable
    os.chmod("./gradlew", 0o755)

    suffix = action
    cmd = ""
    if suffix == "debug":
        cmd = "./gradlew assembleDebug"
    elif suffix == "release":
        cmd = "./gradlew assembleRelease"
    elif suffix == "bundle":
        cmd = "./gradlew bundleRelease"
    else:
        # Default build (assembleDebug)
         cmd = "./gradlew assembleDebug"
    
    print_info(f"Running: {cmd}")
    if run_command(cmd):
        print_success("Build successful.")
        # Print output paths logic could be improved with find, but simple success msg is start.
        if suffix == "debug" or suffix == "build":
            print_success(f"Output: app/build/outputs/apk/debug/app-debug.apk")
        elif suffix == "release":
            print_success(f"Output: app/build/outputs/apk/release/app-release-unsigned.apk (or signed if configured)")
        elif suffix == "bundle":
             print_success(f"Output: app/build/outputs/bundle/release/app-release.aab")
        
        # Verify signature if release
        if suffix == "release":
             out_apk = "app/build/outputs/apk/release/app-release-unsigned.apk" 
             # Note: If signed, AGP might name it differently like input name.
             # Actually standard AGP with signingConfig produces 'app-release.apk'
             if os.path.exists("app/build/outputs/apk/release/app-release.apk"):
                 out_apk = "app/build/outputs/apk/release/app-release.apk"
             
             if os.path.exists(out_apk):
                 verify_apk(out_apk)
             else:
                 print_warning(f"Could not find APK to verify at {out_apk}")
    else:
        print_error("Build failed.")
        sys.exit(1)



def clean():
    """Clean the project"""
    project_root = find_project_root()
    if not project_root:
        print_error("Error: Project root not found.")
        sys.exit(1)
    os.chdir(project_root)

    if not os.path.exists("./gradlew"):
        print_error("Error: gradlew not found.")
        sys.exit(1)
    
    os.chmod("./gradlew", 0o755)
    print_info("Running clean...")
    run_command("./gradlew clean")
    print_success("Clean complete.")



def signing():
    """Configure signing"""
    project_root = find_project_root()
    if not project_root:
        print_error("Error: Project root not found.")
        sys.exit(1)
    os.chdir(project_root)

    print_info("Configuring Signing...")
    props_file = "signing.properties"
    
    if os.path.exists(props_file):
        print_warning(f"'{props_file}' already exists.")
        overwrite = typer.prompt("Overwrite? (y/n): ")
        if overwrite.lower() != 'y':
            return
            
    keystore_path = typer.prompt("Enter path to Keystore (leave empty to generate new): ").strip()
    
    store_password = ""
    key_alias = ""
    key_password = ""
    
    if not keystore_path:
        print_info("Generating new keystore...")
        keystore_path = "release.keystore"
        key_alias = "key0"
        
        # Ideally use getpass.getpass()
        import getpass
        pwd = getpass.getpass("Enter new keystore password: ")
        pwd_confirm = getpass.getpass("Confirm password: ")
        if pwd != pwd_confirm:
            print_error("Passwords do not match.")
            return
        
        store_password = pwd
        key_password = pwd
        
        # dname
        dname = "CN=Android Dev, OU=Ktroid, O=Ktroid, L=Unknown, S=Unknown, C=US"
        
        cmd = (f'keytool -genkey -v -keystore {keystore_path} -alias {key_alias} -keyalg RSA '
               f'-keysize 2048 -validity 10000 -storepass {store_password} -keypass {key_password} '
               f'-dname "{dname}"')
               
        if run_command(cmd):
             print_success(f"Keystore generated at {keystore_path}")
        else:
             print_error("Failed to generate keystore. Ensure 'keytool' (JDK) is in PATH.")
             return
    else:
        import getpass
        store_password = getpass.getpass("Enter keystore password: ")
        key_alias = typer.prompt("Enter key alias: ")
        key_password = getpass.getpass("Enter key password: ")

    # Write properties
    with open(props_file, 'w') as f:
        f.write(f"storeFile={keystore_path}\n")
        f.write(f"storePassword={store_password}\n")
        f.write(f"keyAlias={key_alias}\n")
        f.write(f"keyPassword={key_password}\n")
        
    print_success(f"Signing configured in {props_file}. You can now run 'ktroid build release'.")



def run():
    """Build, Install and Run."""
    project_root = find_project_root()
    if not project_root:
        print_error("Error: Project root not found.")
        sys.exit(1)
    os.chdir(project_root)
    
    # 1. Select Device
    devices = get_connected_devices()
    if not devices:
        print_error("No connected devices found. Connect a device via USB or start emulator.")
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
             
    print_info(f"Target: {target_device}")
    
    # 2. Build Debug
    print_info("Building Debug APK...")
    # Call cmd_build logic? Or invoke gradle directly?
    # Better to invoke existing logic.
    # Re-using cmd_build args shim
    class BuildArgs:
        action = "debug"
    
    try:
         # Use subprocess to call self? No, just call function if possible.
         # But cmd_build expects args object
         # Let's just run gradle directly here for simplicity or simulate
         
         if not os.path.exists("./gradlew"):
             print_error("gradlew not found.")
             return
             
         if not run_command("./gradlew assembleDebug"):
             print_error("Build failed.")
             return
    except Exception as e:
         print_error(f"Build Error: {e}")
         return
         
    # 3. Install
    apk = "app/build/outputs/apk/debug/app-debug.apk"
    if not os.path.exists(apk):
        print_error("APK not found after build.")
        return
        
    print_info("Installing...")
    if not run_command(f"adb -s {target_device} install -r {apk}"):
        print_error("Install failed.")
        return
        
    # 4. Launch
    print_info("Launching...")
    # Need package name / main activity
    # Default: package/.MainActivity
    # We parse package from build.gradle
    app_id = None
    if os.path.exists("app/build.gradle"):
         with open("app/build.gradle", "r") as f:
             cnt = f.read()
             m = re.search(r'applicationId\s+"?([^"\n]+)"?', cnt)
             if m: app_id = m.group(1)
             
    if app_id:
        cmd = f"adb -s {target_device} shell am start -n {app_id}/.MainActivity"
        run_command(cmd)
        print_success("App Launched.")
    else:
        print_warning("Could not determine package name to launch automatically.")



def test(test_type: str = typer.Argument("unit", help="Type of test (unit, instrumented, all)")):
    """Run tests"""
    project_root = find_project_root()
    if not project_root:
        print_error("Error: Project root not found.")
        sys.exit(1)
    os.chdir(project_root)

    if not os.path.exists("./gradlew"):
        print_error("Error: gradlew not found.")
        sys.exit(1)
    
    os.chmod("./gradlew", 0o755)
    
    test_type = test_type
    
    if test_type == "unit":
        print_info("Running unit tests...")
        run_command("./gradlew test")
    elif test_type == "instrumented":
        print_info("Running instrumented tests...")
        run_command("./gradlew connectedAndroidTest")
    else:
        print_info("Running all tests...")
        run_command("./gradlew test connectedAndroidTest")


