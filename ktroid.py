#!/usr/bin/env python3
"""
ktroid: A CLI tool to generate, build, clean, and sign pure native Android projects.
"""

import argparse
import os
import shutil
import subprocess
import sys
import re
import urllib.request
import zipfile
import ssl

# Constants (Defaults)
DEFAULT_CONFIG = {
    "java_version": "17",
    "agp_version": "8.13.2",
    "gradle_version": "9.3.1",
    "kotlin_version": "2.2.21",
    "compile_sdk": "35",
    "min_sdk": "21",
    "target_sdk": "35",
    "build_tools_version": "35.0.0"
}

# Download URLs
CMD_TOOLS_URL = "https://dl.google.com/android/repository/commandlinetools-linux-14742923_latest.zip"
GRADLE_dist_URL = "https://services.gradle.org/distributions/gradle-9.3.1-bin.zip"

# ANSI Colors
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_success(msg):
    print(f"{Colors.OKGREEN}{msg}{Colors.ENDC}")

def print_error(msg):
    print(f"{Colors.FAIL}{msg}{Colors.ENDC}")

def print_warning(msg):
    print(f"{Colors.WARNING}{msg}{Colors.ENDC}")

def print_info(msg):
    print(f"{Colors.OKCYAN}{msg}{Colors.ENDC}")

def get_script_dir():
    return os.path.dirname(os.path.realpath(__file__))

def get_config_dir():
    return get_script_dir()

def load_config():
    """Load config from config.json in script dir or return defaults."""
    config_path = os.path.join(get_config_dir(), "config.json")
    config = DEFAULT_CONFIG.copy()
    
    if os.path.exists(config_path):
        try:
            import json
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                config.update(user_config)
        except Exception as e:
            print_warning(f"Failed to load config file: {e}. Using defaults.")
    
    return config

CONFIG = load_config()

def get_template_path(filename):
    return os.path.join(get_script_dir(), 'templates', filename)

def run_command(command, cwd=None, show_output=True):
    """Run a shell command."""
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=None if show_output else subprocess.PIPE,
            stderr=None if show_output else subprocess.PIPE,
            shell=True,
            text=True
        )
        
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            if not show_output and stderr:
                print_error(f"Command failed: {command}")
                print_error(f"Error output:\n{stderr}")
            return False
            
        return True
    except Exception as e:
        print_error(f"Execution failed: {e}")
        return False

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

def generate_project_structure(project_dir, project_name, package_name):
    """Generates the project files in the given directory."""
    
    # 2. Create Directory Structure
    app_dir = os.path.join(project_dir, 'app')
    src_main_dir = os.path.join(app_dir, 'src', 'main')
    java_dir = os.path.join(src_main_dir, 'java', *package_name.split('.'))
    res_dir = os.path.join(src_main_dir, 'res')
    values_dir = os.path.join(res_dir, 'values')
    xml_dir = os.path.join(res_dir, 'xml')
    drawable_dir = os.path.join(res_dir, 'drawable')

    os.makedirs(java_dir, exist_ok=True)
    os.makedirs(values_dir, exist_ok=True)
    os.makedirs(xml_dir, exist_ok=True)
    os.makedirs(drawable_dir, exist_ok=True)

    # 3. Copy/Render Templates
    def render_template(template_name, dest_path):
        with open(get_template_path(template_name), 'r') as f:
            content = f.read()
        
        # Replacements
        replacements = {
            '{project_name}': project_name,
            '{package_name}': package_name,
            '{package_path}': package_name.replace('.', '/'),
            '8.13.2': CONFIG['agp_version'], 
            '2.2.21': CONFIG['kotlin_version'],
            '{agp_version}': CONFIG['agp_version'], 
            '{kotlin_version}': CONFIG['kotlin_version'],
            '{compile_sdk}': CONFIG['compile_sdk'],
            '{min_sdk}': CONFIG['min_sdk'],
            '{target_sdk}': CONFIG['target_sdk'],
            '{version_code}': "1",
            '{version_name}': "1.0",
            '{java_version}': CONFIG['java_version']
        }

        for k, v in replacements.items():
            content = content.replace(k, str(v))
        
        with open(dest_path, 'w') as f:
            f.write(content)

    render_template('settings.gradle', os.path.join(project_dir, 'settings.gradle'))
    render_template('root_build.gradle', os.path.join(project_dir, 'build.gradle'))
    render_template('gitignore', os.path.join(project_dir, '.gitignore'))
    render_template('gradle.properties', os.path.join(project_dir, 'gradle.properties'))
    render_template('project_readme.md', os.path.join(project_dir, 'README.md'))
    
    render_template('app_build.gradle', os.path.join(app_dir, 'build.gradle'))
    render_template('proguard-rules.pro', os.path.join(app_dir, 'proguard-rules.pro'))
    
    render_template('AndroidManifest.xml', os.path.join(src_main_dir, 'AndroidManifest.xml'))
    render_template('MainActivity.kt', os.path.join(java_dir, 'MainActivity.kt'))
    
    render_template('colors.xml', os.path.join(values_dir, 'colors.xml'))
    render_template('strings.xml', os.path.join(values_dir, 'strings.xml'))
    render_template('themes.xml', os.path.join(values_dir, 'themes.xml'))
    
    render_template('data_extraction_rules.xml', os.path.join(xml_dir, 'data_extraction_rules.xml'))
    render_template('backup_rules.xml', os.path.join(xml_dir, 'backup_rules.xml'))
    
    # Splash & Logo
    render_template('splash_background.xml', os.path.join(drawable_dir, 'splash_background.xml'))
    
    # Copy Logo
    logo_src = os.path.join(get_script_dir(), 'img', 'logo.png')
    if os.path.exists(logo_src):
        shutil.copy(logo_src, os.path.join(drawable_dir, 'logo.png'))
        print_info("Applied custom logo and splash screen.")
    else:
        print_warning("Warning: img/logo.png not found. App icon might be missing.")
    
    # 4. Generate Wrapper
    print_info("Generating Gradle wrapper...")
    if shutil.which("gradle"):
        cmd = f"gradle wrapper --gradle-version {CONFIG['gradle_version']}"
        if not run_command(cmd, cwd=project_dir, show_output=False):
             print_warning("Warning: Failed to generate gradle wrapper.")
    else:
        print_error("Error: System 'gradle' not found. Cannot generate wrapper offline without it.")

    print_success(f"Project '{project_name}' configured successfully.")

def cmd_create(args):
    """Create a new Android project."""
    project_name = args.project_name
    
    if args.package_name:
        package_name = args.package_name
    else:
        package_name = f"com.example.{project_name.lower()}"
        
    project_dir = os.path.join(os.getcwd(), project_name)

    if os.path.exists(project_dir):
        print_error(f"Error: Directory '{project_name}' already exists.")
        sys.exit(1)

    print_info(f"Creating project '{project_name}' at {project_dir}...")
    print_info(f"Package: {package_name}")
    
    os.makedirs(project_dir)
    generate_project_structure(project_dir, project_name, package_name)

def cmd_init(args):
    """Initialize a project in the current directory."""
    cwd = os.getcwd()
    default_name = os.path.basename(cwd)
    
    # Interactive Prompts
    project_name = input(f"Project Name [{default_name}]: ").strip() or default_name
    default_package = f"com.example.{project_name.lower()}"
    package_name = input(f"Package Name [{default_package}]: ").strip() or default_package
    
    print_info(f"Initializing project '{project_name}' in current directory...")
    
    # Safety Check: Warn if directory is clear
    if os.listdir(cwd):
        print_warning("Warning: Current directory is NOT empty.")
        confirm = input("Continue anyway? (y/n): ")
        if confirm.lower() != 'y':
            print_info("Aborting.")
            return

    generate_project_structure(cwd, project_name, package_name)

def cmd_build(args):
    """Run build commands using glob wrapper."""
    if not os.path.exists("./gradlew"):
        print_error("Error: gradlew not found. Are you in the project root?")
        sys.exit(1)

    # Ensure executable
    os.chmod("./gradlew", 0o755)

    suffix = args.action
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

def cmd_clean(args):
    """Run gradlew clean."""
    if not os.path.exists("./gradlew"):
        print_error("Error: gradlew not found.")
        sys.exit(1)
    
    os.chmod("./gradlew", 0o755)
    print_info("Running clean...")
    run_command("./gradlew clean")
    print_success("Clean complete.")

def cmd_signing(args):
    """Configure signing."""
    print_info("Configuring Signing...")
    props_file = "signing.properties"
    
    if os.path.exists(props_file):
        print_warning(f"'{props_file}' already exists.")
        overwrite = input("Overwrite? (y/n): ")
        if overwrite.lower() != 'y':
            return
            
    keystore_path = input("Enter path to Keystore (leave empty to generate new): ").strip()
    
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
        key_alias = input("Enter key alias: ")
        key_password = getpass.getpass("Enter key password: ")

    # Write properties
    with open(props_file, 'w') as f:
        f.write(f"storeFile={keystore_path}\n")
        f.write(f"storePassword={store_password}\n")
        f.write(f"keyAlias={key_alias}\n")
        f.write(f"keyPassword={key_password}\n")
        
    print_success(f"Signing configured in {props_file}. You can now run 'ktroid build release'.")

def cmd_info(args):
    """Extract info from build.gradle."""
    build_file = "app/build.gradle"
    if not os.path.exists(build_file):
        print("Error: app/build.gradle not found.")
        sys.exit(1)
        
    with open(build_file, 'r') as f:
        content = f.read()
        
    def find_val(key):
        match = re.search(fr'{key}\s+"?([^"\n]+)"?', content)
        if match: return match.group(1)
        # Try = style
        match = re.search(fr'{key}\s*=\s*"?([^"\n]+)"?', content)
        if match: return match.group(1)
        return "Unknown"

    print("Project Info:")
    print(f"  Application ID: {find_val('applicationId')}")
    print(f"  Version Code:   {find_val('versionCode')}")
    print(f"  Version Name:   {find_val('versionName')}")
    print(f"  Min SDK:        {find_val('minSdk')}")
    print(f"  Target SDK:     {find_val('targetSdk')}")
    print(f"  Compile SDK:    {find_val('compileSdk')}")

def cmd_config(args):
    """Generate default configuration file."""
    config_dir = get_config_dir()
    config_path = os.path.join(config_dir, "config.json")
    
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
        
    if os.path.exists(config_path) and not args.init:
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

def cmd_setup(args):
    """Setup Android SDK and Gradle with interactive feedback."""
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

def cmd_dep(args):
    """Manage dependencies."""
    if not args.name:
        print_info("Available Shortcuts:")
        for k, v in COMMON_DEPS.items():
            print(f"  {k:<12} -> {v}")
        print("\nUsage:")
        print("  ktroid dep <shortcut>   (e.g., ktroid dep glide)")
        print("  ktroid dep <coord>      (e.g., ktroid dep com.foo:bar:1.2)")
        return

    dep_str = COMMON_DEPS.get(args.name.lower(), args.name)
    build_file = "app/build.gradle"
    
    if not os.path.exists(build_file):
        print_error("Error: app/build.gradle not found.")
        return

    print_info(f"Adding dependency: {dep_str}")
    
    with open(build_file, "r") as f:
        lines = f.readlines()
        
    new_lines = []
    in_dependencies = False
    added = False
    
    for line in lines:
        new_lines.append(line)
        if "dependencies {" in line:
            in_dependencies = True
        
        if in_dependencies and "}" in line and not added:
             # Add before closing brace
             # Remove the brace we just added to strict logic
             new_lines.pop()
             new_lines.append(f"    implementation '{dep_str}'\n")
             new_lines.append(line)
             added = True
             in_dependencies = False
             
    with open(build_file, "w") as f:
        f.writelines(new_lines)
        
    print_success("Dependency added successfully.")

def cmd_perm(args):
    """Add permissions."""
    if not args.name:
        print_info("Common Permissions:")
        for k, v in COMMON_PERMS.items():
            print(f"  {k:<18} -> {v}")
        print("\nUsage: ktroid perm <name>")
        return

    perm_name = COMMON_PERMS.get(args.name.lower())
    if not perm_name:
         # Assume user knows what they are doing if not in list
         if "." in args.name:
             perm_name = args.name
         else:
             print_error(f"Unknown permission shortcut: {args.name}")
             return

    manifest_file = "app/src/main/AndroidManifest.xml"
    if not os.path.exists(manifest_file):
        print_error("Error: AndroidManifest.xml not found.")
        return
        
    print_info(f"Adding permission: {perm_name}")
    
    with open(manifest_file, "r") as f:
        lines = f.readlines()
        
    # check if already exists
    for line in lines:
        if perm_name in line:
            print_warning("Permission already exists.")
            return

    new_lines = []
    added = False
    
    for line in lines:
        # Insert before <application
        if "<application" in line and not added:
            new_lines.append(f'    <uses-permission android:name="{perm_name}" />\n')
            added = True
        new_lines.append(line)
        
    with open(manifest_file, "w") as f:
        f.writelines(new_lines)
        
    print_success("Permission added.")

def cmd_logo(args):
    """Change app logo with multiple density support."""
    src_image = args.path
    if not os.path.exists(src_image):
        print_error(f"Error: Image '{src_image}' not found.")
        return

    res_dir = "app/src/main/res"
    if not os.path.exists(res_dir):
        print_error("Error: Project structure not found (res/ missing).")
        return
    
    # Check if PIL/Pillow is available for resizing
    try:
        from PIL import Image
        has_pil = True
    except ImportError:
        has_pil = False
        print_warning("PIL/Pillow not found. Installing single logo without density variants.")
    
    if has_pil:
        # Generate multiple densities
        densities = {
            "mdpi": 48,
            "hdpi": 72,
            "xhdpi": 96,
            "xxhdpi": 144,
            "xxxhdpi": 192
        }
        
        print_info("Generating app icons for multiple densities...")
        
        try:
            img = Image.open(src_image)
            
            # Convert to RGBA if needed
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            for density, size in densities.items():
                # Create density folder
                density_dir = os.path.join(res_dir, f"mipmap-{density}")
                os.makedirs(density_dir, exist_ok=True)
                
                # Resize and save
                resized = img.resize((size, size), Image.Resampling.LANCZOS)
                output_path = os.path.join(density_dir, "ic_launcher.png")
                resized.save(output_path, "PNG")
                print_success(f"  ✓ {density}: {size}x{size}px")
            
            # Also copy to drawable for backward compatibility
            drawable_dir = os.path.join(res_dir, "drawable")
            os.makedirs(drawable_dir, exist_ok=True)
            resized_96 = img.resize((96, 96), Image.Resampling.LANCZOS)
            resized_96.save(os.path.join(drawable_dir, "logo.png"), "PNG")
            
            print_success("App icon updated for all densities.")
            print_info("Note: Clean and rebuild to see changes.")
            
        except Exception as e:
            print_error(f"Failed to process image: {e}")
    else:
        # Fallback: Just copy to drawable
        dest_dir = os.path.join(res_dir, "drawable")
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, "logo.png")
        
        try:
            shutil.copy(src_image, dest_path)
            print_success(f"Logo updated from {src_image}")
            print_info("Install Pillow for automatic multi-density icon generation: pip install Pillow")
        except Exception as e:
            print_error(f"Failed to copy image: {e}")

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

def cmd_logs(args):
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

def cmd_run(args):
    """Build, Install and Run."""
    
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
             sel = int(input("Select device (number): "))
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

def cmd_emulator(args):
    """Manage Android Emulators."""
    action = args.action
    
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
        if args.name:
            avd_name = args.name
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
                    sel = int(input("Select AVD (number): "))
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
        
        avd_name = input("AVD Name [Pixel_API_35]: ").strip() or "Pixel_API_35"
        device_type = input("Device Type [pixel_7]: ").strip() or "pixel_7"
        system_image = input("System Image [system-images;android-35;google_apis;x86_64]: ").strip() or "system-images;android-35;google_apis;x86_64"
        
        # Check if image is installed
        print_info(f"Checking if system image is installed...")
        try:
            result = subprocess.run(["sdkmanager", "--list_installed"], capture_output=True, text=True)
            if system_image not in result.stdout:
                print_warning(f"System image not installed: {system_image}")
                confirm = input("Install now? (y/n): ")
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

def cmd_install(args):
    """Install an APK to device."""
    apk_path = args.apk_path
    
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
            sel = int(input("Select device (number): "))
            target_device = devices[sel-1]
        except:
            print_error("Invalid selection.")
            return
    
    print_info(f"Installing {os.path.basename(apk_path)} to {target_device}...")
    
    if run_command(f"adb -s {target_device} install -r {apk_path}"):
        print_success("APK installed successfully.")
    else:
        print_error("Installation failed.")

def cmd_uninstall(args):
    """Uninstall app from device."""
    
    # Get package name
    package_name = args.package_name
    
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
            sel = int(input("Select device (number): "))
            target_device = devices[sel-1]
        except:
            print_error("Invalid selection.")
            return
    
    print_info(f"Uninstalling {package_name} from {target_device}...")
    
    if run_command(f"adb -s {target_device} uninstall {package_name}"):
        print_success("App uninstalled successfully.")
    else:
        print_error("Uninstallation failed.")

def cmd_test(args):
    """Run tests."""
    if not os.path.exists("./gradlew"):
        print_error("Error: gradlew not found.")
        sys.exit(1)
    
    os.chmod("./gradlew", 0o755)
    
    test_type = args.test_type if hasattr(args, 'test_type') else "unit"
    
    if test_type == "unit":
        print_info("Running unit tests...")
        run_command("./gradlew test")
    elif test_type == "instrumented":
        print_info("Running instrumented tests...")
        run_command("./gradlew connectedAndroidTest")
    else:
        print_info("Running all tests...")
        run_command("./gradlew test connectedAndroidTest")

def cmd_bump(args):
    """Bump version code/name."""
    build_file = "app/build.gradle"
    
    if not os.path.exists(build_file):
        print_error("app/build.gradle not found.")
        return
    
    with open(build_file, 'r') as f:
        content = f.read()
    
    bump_type = args.bump_type
    
    if bump_type == "code" or bump_type == "both":
        # Bump version code
        match = re.search(r'versionCode\s+(\d+)', content)
        if match:
            old_code = int(match.group(1))
            new_code = old_code + 1
            content = re.sub(r'versionCode\s+\d+', f'versionCode {new_code}', content)
            print_success(f"Version code: {old_code} -> {new_code}")
        else:
            print_warning("Could not find versionCode in build.gradle")
    
    if bump_type == "name" or bump_type == "both":
        # Bump version name
        match = re.search(r'versionName\s+"([^"]+)"', content)
        if match:
            old_name = match.group(1)
            parts = old_name.split('.')
            
            if len(parts) >= 3:
                # Increment patch version
                parts[-1] = str(int(parts[-1]) + 1)
                new_name = '.'.join(parts)
            else:
                # Just increment
                new_name = old_name + ".1"
            
            content = re.sub(r'versionName\s+"[^"]+"', f'versionName "{new_name}"', content)
            print_success(f"Version name: {old_name} -> {new_name}")
        else:
            print_warning("Could not find versionName in build.gradle")
    
    # Write back
    with open(build_file, 'w') as f:
        f.write(content)
    
    print_success("build.gradle updated.")

def cmd_dep_list(args):
    """List all dependencies."""
    build_file = "app/build.gradle"
    
    if not os.path.exists(build_file):
        print_error("app/build.gradle not found.")
        return
    
    with open(build_file, 'r') as f:
        lines = f.readlines()
    
    print_info("Current Dependencies:")
    in_deps = False
    count = 0
    
    for line in lines:
        if "dependencies {" in line:
            in_deps = True
            continue
        
        if in_deps:
            if "}" in line:
                break
            
            # Match implementation, api, etc
            match = re.search(r"(implementation|api|testImplementation|androidTestImplementation)\s+['\"]([^'\"]+)['\"]", line)
            if match:
                dep_type = match.group(1)
                dep_name = match.group(2)
                count += 1
                print(f"  {count}. [{dep_type}] {dep_name}")
    
    if count == 0:
        print_warning("No dependencies found.")

def cmd_dep_remove(args):
    """Remove a dependency."""
    dep_name = args.dep_name
    build_file = "app/build.gradle"
    
    if not os.path.exists(build_file):
        print_error("app/build.gradle not found.")
        return
    
    with open(build_file, 'r') as f:
        lines = f.readlines()
    
    new_lines = []
    removed = False
    
    for line in lines:
        # Check if line contains the dependency
        if dep_name in line and ("implementation" in line or "api" in line or "testImplementation" in line):
            print_info(f"Removing: {line.strip()}")
            removed = True
            continue
        new_lines.append(line)
    
    if removed:
        with open(build_file, 'w') as f:
            f.writelines(new_lines)
        print_success("Dependency removed.")
    else:
        print_warning(f"Dependency '{dep_name}' not found.")

def cmd_perm_remove(args):
    """Remove a permission."""
    perm_name = args.perm_name
    
    # Check if it's a shortcut
    if perm_name.lower() in COMMON_PERMS:
        perm_name = COMMON_PERMS[perm_name.lower()]
    elif "." not in perm_name:
        print_error(f"Unknown permission: {perm_name}")
        return
    
    manifest_file = "app/src/main/AndroidManifest.xml"
    if not os.path.exists(manifest_file):
        print_error("AndroidManifest.xml not found.")
        return
    
    with open(manifest_file, 'r') as f:
        lines = f.readlines()
    
    new_lines = []
    removed = False
    
    for line in lines:
        if perm_name in line and "uses-permission" in line:
            print_info(f"Removing: {line.strip()}")
            removed = True
            continue
        new_lines.append(line)
    
    if removed:
        with open(manifest_file, 'w') as f:
            f.writelines(new_lines)
        print_success("Permission removed.")
    else:
        print_warning(f"Permission '{perm_name}' not found.")

def cmd_version(args):
    print_info("ktroid version 1.0.0")

def main():
    parser = argparse.ArgumentParser(prog="ktroid", description="CLI tool for native Android development (Kotlin+Gradle).")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Create
    parser_create = subparsers.add_parser("create", help="Create a new project")
    parser_create.add_argument("project_name", help="Name of the project")
    parser_create.add_argument("package_name", nargs="?", help="Optional package name (e.g. com.example.app)")

    # Build
    parser_build = subparsers.add_parser("build", help="Build the project")
    parser_build.add_argument("action", nargs="?", choices=["debug", "release", "bundle"], default="debug", help="Build type")

    # Clean
    parser_clean = subparsers.add_parser("clean", help="Clean the project")

    # Signing
    parser_signing = subparsers.add_parser("signing", help="Configure signing")

    # Setup
    parser_setup = subparsers.add_parser("setup", help="Setup Android Environment")
    
    # Init
    parser_init = subparsers.add_parser("init", help="Initialize project in current dir")

    # Dep
    parser_dep = subparsers.add_parser("dep", help="Manage dependencies")
    parser_dep.add_argument("name", nargs="?", help="Dependency shortcut or coordinate")

    # Perm
    parser_perm = subparsers.add_parser("perm", help="Add permissions")
    parser_perm.add_argument("name", nargs="?", help="Permission shortcut or name")

    # Logo
    parser_logo = subparsers.add_parser("logo", help="Change app logo")
    parser_logo.add_argument("path", help="Path to new logo image")

    # Logs
    parser_logs = subparsers.add_parser("logs", help="View filtered logcat")

    # Run
    parser_run = subparsers.add_parser("run", help="Build, Install and Run on device")

    # Config
    parser_config = subparsers.add_parser("config", help="Manage configuration")
    parser_config.add_argument("--init", action="store_true", help="Reset/Create default config file")

    # Check
    parser_check = subparsers.add_parser("check", help="Check dependencies")
    parser.add_argument("--check", action="store_true", help="Check dependencies")
    parser.add_argument("--version", action="store_true", help="Show version")

    # Info
    parser_info = subparsers.add_parser("info", help="Show project info")
    
    # Emulator
    parser_emulator = subparsers.add_parser("emulator", help="Manage emulators")
    parser_emulator.add_argument("action", choices=["list", "start", "create"], help="Emulator action")
    parser_emulator.add_argument("name", nargs="?", help="AVD name (for start)")
    
    # Install
    parser_install = subparsers.add_parser("install", help="Install APK to device")
    parser_install.add_argument("apk_path", help="Path to APK file")
    
    # Uninstall
    parser_uninstall = subparsers.add_parser("uninstall", help="Uninstall app from device")
    parser_uninstall.add_argument("package_name", nargs="?", help="Package name (optional if in project)")
    
    # Test
    parser_test = subparsers.add_parser("test", help="Run tests")
    parser_test.add_argument("test_type", nargs="?", choices=["unit", "instrumented", "all"], default="unit", help="Test type")
    
    # Bump
    parser_bump = subparsers.add_parser("bump", help="Bump version")
    parser_bump.add_argument("bump_type", choices=["code", "name", "both"], default="code", help="What to bump")
    
    # Dep List
    parser_dep_list = subparsers.add_parser("dep-list", help="List dependencies")
    
    # Dep Remove
    parser_dep_remove = subparsers.add_parser("dep-remove", help="Remove dependency")
    parser_dep_remove.add_argument("dep_name", help="Dependency name/pattern to remove")
    
    # Perm Remove
    parser_perm_remove = subparsers.add_parser("perm-remove", help="Remove permission")
    parser_perm_remove.add_argument("perm_name", help="Permission name/shortcut to remove")

    args = parser.parse_args()

    # Handle flag-based commands
    if args.check:
        check_env()
        return
    if args.version:
        cmd_version(args)
        return

    if args.command == "create":
        cmd_create(args)
    elif args.command == "build":
        cmd_build(args)
    elif args.command == "clean":
        cmd_clean(args)
    elif args.command == "signing":
        cmd_signing(args)
    elif args.command == "info":
        cmd_info(args)
    elif args.command == "config":
        cmd_config(args)
    elif args.command == "setup":
        cmd_setup(args)
    elif args.command == "init":
        cmd_init(args)
    elif args.command == "dep":
        cmd_dep(args)
    elif args.command == "dep-list":
        cmd_dep_list(args)
    elif args.command == "dep-remove":
        cmd_dep_remove(args)
    elif args.command == "perm":
        cmd_perm(args)
    elif args.command == "perm-remove":
        cmd_perm_remove(args)
    elif args.command == "logo":
        cmd_logo(args)
    elif args.command == "logs":
        cmd_logs(args)
    elif args.command == "run":
        cmd_run(args)
    elif args.command == "emulator":
        cmd_emulator(args)
    elif args.command == "install":
        cmd_install(args)
    elif args.command == "uninstall":
        cmd_uninstall(args)
    elif args.command == "test":
        cmd_test(args)
    elif args.command == "bump":
        cmd_bump(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
