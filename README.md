# ktroid ⚡
**The Ultimate CLI for Native Android Development**

`ktroid` is a powerful, lightweight command-line interface for building Native Android apps (Kotlin + Gradle). It completely replaces the need for Android Studio, allowing you to develop, build, sign, and deploy apps directly from your terminal.

## 🚀 Features

*   **Zero Bloat**: No 2GB IDE RAM usage. Works on low-end hardware.
*   **Smart Setup**: Automatically installs Java, Gradle, and SDK Tools.
*   **Offline First**: Built for developers with limited internet.
*   **Instant Run**: Build, Install, and Launch with one command.
*   **Emulator Management**: Create, list, and start Android emulators.
*   **Coding Assistants**: Shortcuts for Dependencies and Permissions.
*   **Smart Logging**: Clean, app-specific logcat viewer.
*   **Test Runner**: Run unit and instrumented tests easily.
*   **Version Management**: Auto-bump version codes and names.
*   **Multi-Density Icons**: Generate adaptive icons for all screen densities.

## 📦 Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/yourusername/ktroid.git
    cd ktroid
    ```
2.  Run Setup Wizard:
    ```bash
    ./ktroid.py setup
    ```
    *This will check your system for Java/Gradle/SDK and install anything missing.*
    
3.  (Optional) Install Pillow for multi-density icon generation:
    ```bash
    pip install Pillow
    ```

## ⚡ Quick Start

### 1. Initialize Project
Go to your project folder (or create one):
```bash
./ktroid.py init
```
*Follow the interactive prompts to set your App Name and Package.*

### 2. Build & Run
Connect your phone via USB and run:
```bash
./ktroid.py run
```
*This selects your device, builds the app, installs it, and launches it automatically.*

---

## 🛠 Command Reference

### Project Management

#### Create New Project (`ktroid create`)
Create a new Android project with custom name and package.
```bash
./ktroid.py create MyApp com.example.myapp
```

#### Initialize in Current Directory (`ktroid init`)
Set up Android project structure in the current folder.
```bash
./ktroid.py init
```

#### Project Info (`ktroid info`)
Display project configuration (package, versions, SDK levels).
```bash
./ktroid.py info
```

---

### Build & Deploy

#### Build (`ktroid build`)
Build your app in different configurations.
```bash
./ktroid.py build debug          # Debug APK
./ktroid.py build release        # Signed Release APK
./ktroid.py build bundle         # Android App Bundle (AAB)
```

#### Clean (`ktroid clean`)
Clean build artifacts.
```bash
./ktroid.py clean
```

#### Run (`ktroid run`)
Build, install, and launch app on connected device.
```bash
./ktroid.py run
```

#### Install APK (`ktroid install`)
Install an existing APK to a device.
```bash
./ktroid.py install app-debug.apk
```

#### Uninstall App (`ktroid uninstall`)
Remove app from device.
```bash
./ktroid.py uninstall              # Uses project package name
./ktroid.py uninstall com.example.app  # Specify package
```

---

### Emulator Management

#### List Emulators (`ktroid emulator list`)
Show all available Android Virtual Devices (AVDs).
```bash
./ktroid.py emulator list
```

#### Start Emulator (`ktroid emulator start`)
Launch an Android emulator.
```bash
./ktroid.py emulator start           # Interactive selection
./ktroid.py emulator start Pixel_7   # Start specific AVD
```

#### Create Emulator (`ktroid emulator create`)
Create a new Android Virtual Device.
```bash
./ktroid.py emulator create
```
*Follow the interactive prompts for AVD name, device type, and system image.*

---

### Development Shortcuts

#### Dependency Manager (`ktroid dep`)
Add libraries without searching for version numbers.
*   **List common libs**:
    ```bash
    ./ktroid.py dep
    ```
*   **Add Library**:
    ```bash
    ./ktroid.py dep glide      # Adds Glide
    ./ktroid.py dep retrofit   # Adds Retrofit
    ./ktroid.py dep androidx.navigation:navigation-compose:2.7.5
    ```

#### List Dependencies (`ktroid dep-list`)
View all current dependencies in your project.
```bash
./ktroid.py dep-list
```

#### Remove Dependency (`ktroid dep-remove`)
Remove a dependency from build.gradle.
```bash
./ktroid.py dep-remove glide
./ktroid.py dep-remove retrofit
```

---

### Permission Manager

#### Add Permission (`ktroid perm`)
Inject permissions into `AndroidManifest.xml`.
*   **Add Permission**:
    ```bash
    ./ktroid.py perm internet
    ./ktroid.py perm camera
    ./ktroid.py perm android.permission.ACCESS_FINE_LOCATION
    ```

#### Remove Permission (`ktroid perm-remove`)
Remove a permission from manifest.
```bash
./ktroid.py perm-remove internet
./ktroid.py perm-remove camera
```

---

### Asset Management

#### Icon Changer (`ktroid logo`)
Replace the default app icon with automatic multi-density generation.
```bash
./ktroid.py logo /path/to/my_icon.png
```
*Automatically generates icons for mdpi, hdpi, xhdpi, xxhdpi, xxxhdpi if Pillow is installed.*

---

### Testing

#### Run Tests (`ktroid test`)
Execute unit and instrumented tests.
```bash
./ktroid.py test                # Unit tests
./ktroid.py test unit           # Unit tests only
./ktroid.py test instrumented   # Instrumented tests
./ktroid.py test all            # All tests
```

---

### Debugging

#### Smart Logs (`ktroid logs`)
View logs **only** for your app, filtered by process ID. No system noise.
```bash
./ktroid.py logs
```

---

### Version Management

#### Bump Version (`ktroid bump`)
Automatically increment version code or name.
```bash
./ktroid.py bump code    # Increment versionCode (1 -> 2)
./ktroid.py bump name    # Increment versionName (1.0 -> 1.1)
./ktroid.py bump both    # Increment both
```

---

### Production

#### Signing (`ktroid signing`)
Generate a secure keystore for the Play Store.
```bash
./ktroid.py signing
```

#### Release Build
Build a signed, optimized APK. The tool automatically verifies the signature.
```bash
./ktroid.py build release
```

---

### Environment

#### Check Dependencies (`ktroid --check`)
Verify Java, Gradle, Android SDK, and ADB installation.
```bash
./ktroid.py --check
```

#### Setup Wizard (`ktroid setup`)
Interactive installer for Android SDK and Gradle.
```bash
./ktroid.py setup
```

#### Configuration (`ktroid config`)
View or reset configuration file.
```bash
./ktroid.py config          # View current config
./ktroid.py config --init   # Reset to defaults
```

---

## ⚙️ Configuration
All versions (AGP, Kotlin, SDK) are managed in `config.json`.
```json
{
    "java_version": "17",
    "agp_version": "8.13.2",
    "gradle_version": "9.2.1",
    "kotlin_version": "2.2.21",
    "compile_sdk": "35",
    "min_sdk": "21",
    "target_sdk": "35",
    "build_tools_version": "35.0.0"
}
```
*Modify this file to update your toolchain without changing code.*

---

## 📚 Common Workflows

### Starting a New Project
```bash
# Create project
./ktroid.py create MyAwesomeApp com.mycompany.awesome

# Navigate to project
cd MyAwesomeApp

# Add dependencies
./ktroid.py dep retrofit
./ktroid.py dep room

# Add permissions
./ktroid.py perm internet
./ktroid.py perm storage

# Build and run
./ktroid.py run
```

### Release Workflow
```bash
# Configure signing
./ktroid.py signing

# Bump version
./ktroid.py bump both

# Build release
./ktroid.py build release

# Output: app/build/outputs/apk/release/app-release.apk
```

### Testing Workflow
```bash
# Run unit tests
./ktroid.py test unit

# Run on device
./ktroid.py run

# Check logs
./ktroid.py logs
```

---

## 🎯 Keyboard Shortcuts & Tips

### Speed Tips
- Use `ktroid run` for rapid iteration (build + install + launch)
- Keep `ktroid logs` running in a separate terminal
- Use `ktroid dep-list` before adding dependencies to avoid duplicates
- Run `ktroid bump both` before each release build

### Troubleshooting
- If build fails, run `./ktroid.py clean` first
- For emulator issues, check `adb devices` output
- Verify environment with `./ktroid.py --check`
- Check `signing.properties` exists for release builds

---

## 🤝 Contribution
Open an issue or PR to suggest more "Smart Features"!

---

## 📝 Version History

### v1.0.0 (Current)
- ✅ Fixed critical duplicate code bugs
- ✅ Added emulator management (list, start, create)
- ✅ Added install/uninstall commands
- ✅ Added dependency list and remove
- ✅ Added permission remove
- ✅ Added test runner
- ✅ Added version bump command
- ✅ Improved icon handling with multi-density support
- ✅ Fixed Gradle URL mismatch

### v0.3.0
- Initial stable release
- Core project management
- Build system integration
- Smart dependency and permission management
