
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



def setup():
    """Setup Android Environment."""
    print_info("=== ktroid Setup Wizard ===")
    
    # 1. Define Dependencies
    print_info("\nRequired Dependencies:")
    print("1. Java JDK 17+ (Required to run Gradle/Android tools)")
    print("2. Gradle (Build Tool)")
    print("3. Android Command Line Tools (sdkmanager, apksigner, etc.)")
    print("----------------------------------------------------------")

    dest_root = os.path.expanduser("~/android")
    
    # --- Helper Functions ---
    def install_component(name, url, dest_folder, verify_func):
        # 1. Check
        sys.stdout.write(f"Checking {name}...")
        sys.stdout.flush()
        
        if verify_func(silent=True):
             sys.stdout.write(f"\r[{name}] Status: INSTALLED [ OK ]       \n")
             return True
        
        sys.stdout.write(f"\r[{name}] Status: MISSING                  \n")
             
        # 2. Prompt
        print_info(f"-> {name} is required.")
        print(f"   Download URL: {url}")
        print(f"   Target: {dest_folder}")
        
        confirm = input(f"   Download and install {name}? (y/n): ")
        if confirm.lower() != 'y':
            print_warning(f"   Skipping {name}.")
            return False
            
        # 3. Setup Dir
        os.makedirs(dest_root, exist_ok=True)
            
        # 4. Download
        filename = url.split("/")[-1]
        filepath = os.path.join(dest_root, filename)
        
        if not os.path.exists(filepath):
            print(f"   Downloading {filename}...")
            try:
                urllib.request.urlretrieve(url, filepath, download_progress_hook)
                print() # Newline after progress
            except Exception as e:
                print_error(f"\n   Download failed: {e}")
                return False
        
        print(f"   Extracting {filename}...")
        try:
             with zipfile.ZipFile(filepath, 'r') as zip_ref:
                zip_ref.extractall(dest_folder)
             print_success("   Extraction complete. [ OK ]")
        except Exception as e:
             print_error(f"   Extraction failed: {e}")
             return False
             
        return True

    # --- 0. Java Check (Prerequisite) ---
    sys.stdout.write("Checking Java JDK...")
    sys.stdout.flush()
    if shutil.which("java"):
        sys.stdout.write("\r[Java JDK] Status: INSTALLED [ OK ]          \n")
    else:
        sys.stdout.write("\r[Java JDK] Status: MISSING (Please install JDK 17 manualy) \n")
        print_warning("   Warning: Java is required for Gradle and Android Tools.")

    # --- 1. Gradle Setup ---
    def verify_gradle(silent=False):
        # 1. Check System PATH
        if shutil.which("gradle"):
            return True

        # 2. Check ~/android
        if os.path.exists(dest_root):
            g_dirs = [d for d in os.listdir(dest_root) if d.startswith("gradle-") and os.path.isdir(os.path.join(dest_root, d))]
            if g_dirs:
                # We found a folder, assume it matches if it has bin/gradle
                latest_gradle = sorted(g_dirs)[-1]
                gradle_bin = os.path.join(dest_root, latest_gradle, "bin", "gradle")
                if os.path.exists(gradle_bin):
                    return True
        return False

    if install_component("Gradle", GRADLE_DIST_URL, dest_root, verify_gradle):
         # Post-install verify
         if not verify_gradle(silent=True) and not shutil.which("gradle"):
             # It might be installed but not in PATH for this session
             pass

    # --- 2. CommandLine Tools Setup ---
    def verify_cmdline(silent=False):
        # 1. Check System PATH
        if shutil.which("sdkmanager"):
             return True

        # 2. Check ~/android
        sdkmanager = os.path.join(dest_root, "cmdline-tools", "latest", "bin", "sdkmanager")
        if os.path.exists(sdkmanager): return True
        return False

    if install_component("Android SDK Tools", CMD_TOOLS_URL, dest_root, verify_cmdline):
         # Fix folder structure logic
         base_cmd = os.path.join(dest_root, "cmdline-tools")
         original_bin = os.path.join(base_cmd, "bin") # Extracted as cmdline-tools/bin
         
         if os.path.exists(original_bin):
              print_info("   Structuring SDK correctly (cmdline-tools/latest)...")
              latest_dir = os.path.join(base_cmd, "latest")
              temp_dir = os.path.join(base_cmd, "temp_move")
              
              if not os.path.exists(latest_dir):
                  os.rename(base_cmd, temp_dir)
                  os.makedirs(base_cmd)
                  os.rename(temp_dir, latest_dir)
                  print_success("   Structure fixed. [ OK ]")

    # --- Final Path Exports ---
    print("\n------------------------------------------------")
    print_info("Setup Summary & Exports")
    print("------------------------------------------------")
    
    bashrc_content = []
    
    # Check what we have found/installed to print exports
    # 1. Android Home
    if os.path.exists(dest_root):
         print(f"export ANDROID_HOME=\"{dest_root}\"")
         bashrc_content.append(f'export ANDROID_HOME="{dest_root}"')
    
    # 2. Cmdline Tools
    cmd_bin = os.path.join(dest_root, "cmdline-tools", "latest", "bin")
    if os.path.exists(cmd_bin):
         print(f"export PATH=\"$PATH:{cmd_bin}\"")
         bashrc_content.append(f'export PATH="$PATH:{cmd_bin}"')
    
    # 3. Platform Tools
    plat_bin = os.path.join(dest_root, "platform-tools")
    if os.path.exists(plat_bin):
         print(f"export PATH=\"$PATH:{plat_bin}\"")
         bashrc_content.append(f'export PATH="$PATH:{plat_bin}"')

    # 4. Gradle
    g_dirs = []
    if os.path.exists(dest_root):
        g_dirs = [d for d in os.listdir(dest_root) if d.startswith("gradle-")]
        
    if g_dirs:
         g_bin = os.path.join(dest_root, sorted(g_dirs)[-1], "bin")
         print(f"export PATH=\"$PATH:{g_bin}\"")
         bashrc_content.append(f'export PATH="$PATH:{g_bin}"')
    
    print("\nTo make these permanent, add them to ~/.bashrc")

# --- Advanced Features: Dictionaries ---
COMMON_DEPS = {
    "retrofit": "com.squareup.retrofit2:retrofit:2.9.0",
    "gson": "com.google.code.gson:gson:2.10.1",
    "glide": "com.github.bumptech.glide:glide:4.16.0",
    "coil": "io.coil-kt:coil-compose:2.5.0",
    "navigation": "androidx.navigation:navigation-compose:2.7.5",
    "lifecycle": "androidx.lifecycle:lifecycle-runtime-ktx:2.6.2",
    "coroutines": "org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3",
    "okhttp": "com.squareup.okhttp3:okhttp:4.12.0",
    "material": "com.google.android.material:material:1.11.0",
    "room": "androidx.room:room-runtime:2.6.1"
}

COMMON_PERMS = {
    "internet": "android.permission.INTERNET",
    "camera": "android.permission.CAMERA",
    "storage": "android.permission.WRITE_EXTERNAL_STORAGE",
    "read_storage": "android.permission.READ_EXTERNAL_STORAGE",
    "location": "android.permission.ACCESS_FINE_LOCATION",
    "background_location": "android.permission.ACCESS_BACKGROUND_LOCATION",
    "network_state": "android.permission.ACCESS_NETWORK_STATE",
    "wifi_state": "android.permission.ACCESS_WIFI_STATE",
    "bluetooth": "android.permission.BLUETOOTH",
    "record_audio": "android.permission.RECORD_AUDIO"
}



def config(init: bool = typer.Option(False, "--init", help="Reset config to defaults")):
    """Manage configuration"""
    config_dir = get_config_dir()
    config_path = os.path.join(config_dir, "config.json")
    
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
        
    if os.path.exists(config_path) and not init:
        print_info(f"Configuration file exists at: {config_path}")
        with open(config_path, 'r') as f:
            print(f.read())
        print_info(f"\nEdit this file to update SDK/AGP versions without updating the tool.")
    else:
        if os.path.exists(config_path):
             print_warning("Overwriting existing configuration...")
        
        import json
        with open(config_path, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        print_success(f"Configuration file created at: {config_path}")



def check():
    """Check dependencies"""
    check_env()
