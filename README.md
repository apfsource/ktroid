# ktroid ⚡

A fast, lightweight command-line tool for building Android apps with Kotlin and Gradle. Built for developers who prefer working in the terminal.

![Python](https://img.shields.io/badge/python-3.6+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey.svg)

---

## What is ktroid?

ktroid is a Python-based CLI that handles the entire Android development workflow from your terminal. Instead of waiting for Android Studio to load, you can build, test, and deploy apps with simple commands.

I built this because I got tired of:
- Waiting 30+ seconds for Android Studio to start
- My laptop fan going crazy every time I opened a project
- Clicking through menus just to add a dependency
- Not being able to work on remote servers without X11 forwarding

ktroid works great alongside Android Studio - use AS when you need the visual designer or debugger, and ktroid when you just want to build and test quickly.

---

## Who is this for?

**You'll love ktroid if you:**
- Build and test frequently (multiple times per hour)
- Work on multiple Android projects and switch between them often
- Develop on remote servers or containers
- Set up CI/CD pipelines
- Prefer Vim, Neovim, or VS Code for editing code
- Have limited RAM or want to save battery life
- Learn better by seeing actual Gradle commands instead of IDE abstractions

**You might not need ktroid if you:**
- Primarily use Android Studio's visual layout editor
- Rarely build more than once or twice a day
- Don't mind IDE startup times
- Need advanced debugging with breakpoints and watches

---

## Quick Example

Here's what a typical workflow looks like:

```bash
# Create a new project
ktroid create WeatherApp com.mycompany.weather
cd WeatherApp

# Add some libraries
ktroid dep retrofit
ktroid dep room
ktroid dep glide

# Add permissions
ktroid perm internet
ktroid perm location

# Connect your phone and run
ktroid run

# Watch the logs
ktroid logs

# Make some changes, then rebuild
ktroid run
```

That's it. No project sync, no Gradle daemon warmup, no waiting.

---

## Installation

### Quick Install (Recommended)

**Linux and macOS:**
```bash
git clone https://github.com/apfsource/ktroid.git
cd ktroid
chmod +x ktroid.py
sudo ln -s $(pwd)/ktroid.py /usr/local/bin/ktroid
```

Now `ktroid` works from anywhere:
```bash
cd ~/projects/my-app
ktroid run
```

**Don't have sudo access?** Use this instead:
```bash
git clone https://github.com/apfsource/ktroid.git
cd ktroid
chmod +x ktroid.py
mkdir -p ~/.local/bin
ln -s $(pwd)/ktroid.py ~/.local/bin/ktroid
echo 'export PATH="$PATH:$HOME/.local/bin"' >> ~/.bashrc
source ~/.bashrc
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/apfsource/ktroid.git
cd ktroid

# Create batch wrapper
@"
@echo off
python "%~dp0ktroid.py" %*
"@ | Out-File -FilePath ktroid.bat -Encoding ASCII

# Add to PATH manually through System Properties
# Or use the installer script (coming soon)
```

### First-Time Setup

After installation, run the setup wizard:
```bash
ktroid setup
```

This will:
- Check if Java is installed (downloads OpenJDK if missing)
- Download Android SDK command-line tools
- Install Gradle
- Set up environment variables
- Verify everything works

The whole process takes 5-10 minutes depending on your internet speed.

### Optional: Icon Generation

If you want to use the `ktroid logo` command to generate app icons:
```bash
pip install Pillow
```

This is completely optional - everything else works without it.

---

## Getting Started

### Starting Fresh

Create a new Android project:
```bash
ktroid create MyApp com.example.myapp
cd MyApp
```

This creates a standard Android project structure with:
- Kotlin source files
- Gradle build scripts
- AndroidManifest.xml
- Resource directories
- A simple MainActivity to get you started

### Using an Existing Project

Already have an Android project? Initialize ktroid in it:
```bash
cd /path/to/your/project
ktroid init
```

This sets up ktroid's configuration without touching your existing code.

### Building and Running

Connect your Android phone via USB (make sure USB debugging is enabled):
```bash
ktroid run
```

ktroid will:
1. Detect your connected device
2. Build a debug APK
3. Install it on your device
4. Launch the app
5. Show you the package name and activity

The whole process usually takes 5-15 seconds depending on project size.

### Watching Logs

In a separate terminal, monitor your app's logs:
```bash
ktroid logs
```

This shows only your app's output, filtering out all the system noise. Much cleaner than raw `adb logcat`.

---

## Common Tasks

### Managing Dependencies

**See available shortcuts:**
```bash
ktroid dep
```

This shows popular libraries you can add by name (retrofit, room, glide, etc.).

**Add a library:**
```bash
ktroid dep retrofit
ktroid dep androidx.navigation:navigation-compose:2.7.5
```

**See what's already in your project:**
```bash
ktroid dep-list
```

**Remove a dependency:**
```bash
ktroid dep-remove retrofit
```

### Managing Permissions

**Add a permission:**
```bash
ktroid perm internet
ktroid perm camera
ktroid perm android.permission.ACCESS_FINE_LOCATION
```

Common permissions have shortcuts (internet, camera, storage, location). You can also use the full Android permission name.

**Remove a permission:**
```bash
ktroid perm-remove internet
```

### Building Different Variants

**Debug build (for testing):**
```bash
ktroid build debug
```

**Release build (for production):**
```bash
ktroid build release
```

You'll need to set up signing first (see Production Builds section below).

**Android App Bundle (for Play Store):**
```bash
ktroid build bundle
```

### Changing the App Icon

Replace the default Android icon with your own:
```bash
ktroid logo /path/to/icon.png
```

If you have Pillow installed, this automatically generates icons for all screen densities (mdpi, hdpi, xhdpi, xxhdpi, xxxhdpi). Otherwise, it just copies your icon to the main drawable folder.

### Running Tests

**Run all tests:**
```bash
ktroid test
```

**Just unit tests:**
```bash
ktroid test unit
```

**Just instrumented tests (requires connected device):**
```bash
ktroid test instrumented
```

### Version Management

Bump your app version before releasing:
```bash
ktroid bump code    # 1 -> 2
ktroid bump name    # 1.0 -> 1.1
ktroid bump both    # Increment both
```

This automatically updates `build.gradle`.

### Cleaning Build Files

If something goes wrong, clean everything and start fresh:
```bash
ktroid clean
```

This removes all build artifacts, caches, and generated files.

---

## Working with Emulators

### List Available Emulators

```bash
ktroid emulator list
```

Shows all Android Virtual Devices (AVDs) on your system.

### Start an Emulator

```bash
ktroid emulator start
```

If you have multiple AVDs, ktroid will ask you to choose one. Or specify directly:
```bash
ktroid emulator start Pixel_7
```

### Create a New Emulator

```bash
ktroid emulator create
```

This walks you through:
- Choosing a device type (Pixel, Nexus, etc.)
- Selecting an Android version
- Naming your AVD
- Downloading the system image if needed

---

## Production Builds

### Setting Up Signing

Before you can build a release APK, you need a keystore:
```bash
ktroid signing
```

This creates:
- A secure keystore file (`keystore.jks`)
- A properties file (`signing.properties`) with your credentials

Keep `keystore.jks` safe - you'll need it for all future updates to your app.

### Building for Release

Once signing is configured:
```bash
ktroid build release
```

Your signed APK will be at:
```
app/build/outputs/apk/release/app-release.apk
```

ktroid automatically verifies the signature is valid before finishing.

### Building for Play Store

For Google Play, build an App Bundle instead:
```bash
ktroid build bundle
```

The AAB file will be at:
```
app/build/outputs/bundle/release/app-release.aab
```

---

## Advanced Usage

### Installing Specific APKs

Install any APK to your device:
```bash
ktroid install /path/to/app.apk
```

### Uninstalling Apps

Remove an app from your device:
```bash
ktroid uninstall                    # Uses current project's package
ktroid uninstall com.example.app    # Specify package name
```

### Project Information

See your project's configuration:
```bash
ktroid info
```

Shows:
- Package name
- Version code and name
- Compile, min, and target SDK versions
- Build tools version

### Checking Dependencies

Verify Java, Gradle, and Android SDK are properly installed:
```bash
ktroid --check
```

Useful for troubleshooting environment issues.

### Configuration

View ktroid's configuration:
```bash
ktroid config
```

Reset to defaults:
```bash
ktroid config --init
```

The configuration file (`config.json`) controls:
- Java version
- Gradle version
- Android Gradle Plugin version
- Kotlin version
- SDK versions
- Build tools version

Edit this file to upgrade your toolchain without changing project files.

---

## Real-World Workflows

### Quick Hotfix

You get a bug report about a crash in production:

```bash
cd ~/projects/myapp
git checkout -b hotfix/crash-on-login

# Edit the code in your favorite editor
vim app/src/main/kotlin/LoginActivity.kt

# Test the fix
ktroid run
ktroid logs  # Verify it works

# Run tests
ktroid test unit

# Bump version and build
ktroid bump code
ktroid build release

# Commit and deploy
git commit -am "Fix login crash"
git push
```

Total time: 2-3 minutes instead of 10+ with Android Studio.

### Switching Between Projects

You're working on multiple apps:

```bash
# Morning: Work on App A
cd ~/projects/app-a
ktroid run
ktroid logs &

# Afternoon: Quick fix in App B
cd ~/projects/app-b
ktroid run

# Evening: Back to App A
cd ~/projects/app-a
ktroid run
```

No Android Studio loading screens. No "sync project with Gradle files" delays.

### CI/CD Pipeline

GitHub Actions example:

```yaml
name: Android CI

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up ktroid
        run: |
          git clone https://github.com/apfsource/ktroid.git
          cd ktroid
          chmod +x ktroid.py
          sudo ln -s $(pwd)/ktroid.py /usr/local/bin/ktroid
          ktroid setup
      
      - name: Run tests
        run: ktroid test unit
      
      - name: Build release
        run: ktroid build release
      
      - name: Upload APK
        uses: actions/upload-artifact@v3
        with:
          name: app-release
          path: app/build/outputs/apk/release/app-release.apk
```

### Remote Development

Working on a cloud server without a GUI:

```bash
# On your laptop
ssh user@dev-server

# On the server
cd android-project
ktroid run  # Deploys to your phone connected via adb over network
ktroid logs  # Monitor in real-time
```

---

## Tips and Tricks

### Speed Up Builds

Keep the Gradle daemon running between builds:
```bash
# It starts automatically, but you can verify:
./gradlew --status
```

### Multiple Terminals

I usually have three terminals open:
1. **Main terminal:** Running ktroid commands
2. **Log terminal:** `ktroid logs` running continuously
3. **Editor terminal:** Vim or VS Code

### Aliases

Add these to your `.bashrc` or `.zshrc`:
```bash
alias kr='ktroid run'
alias kl='ktroid logs'
alias kb='ktroid build debug'
alias kt='ktroid test unit'
```

Now you can just type `kr` to build and run.

### Device Selection

If you have multiple devices connected, ktroid will ask you to choose. To skip the prompt, use `adb` to select beforehand:
```bash
adb devices  # See connected devices
export ANDROID_SERIAL=device_id  # Set default device
ktroid run  # Uses that device automatically
```

### Offline Development

After initial setup, ktroid works offline. The SDK, Gradle, and dependencies are cached locally.

### Learning Gradle

Unlike Android Studio which hides Gradle details, ktroid shows you the actual commands it runs. Great for understanding how Android builds work.

---

## Troubleshooting

### "Permission denied" when running ktroid.py

```bash
chmod +x ktroid.py
```

### "Java not found" or "ANDROID_HOME not set"

```bash
ktroid setup
```

This fixes most environment issues.

### Build fails with "Gradle daemon disappeared"

```bash
ktroid clean
./gradlew --stop
ktroid build debug
```

### Device not showing up

1. Enable USB Debugging on your phone
2. Check the cable (some cables are charge-only)
3. Run `adb devices` to verify connection
4. Try `adb kill-server && adb start-server`

### "Pillow not installed" when using logo command

```bash
pip install Pillow
```

Or just manually copy your icon to:
```
app/src/main/res/drawable/ic_launcher.png
```

### Build is slow

First build is always slower (Gradle needs to download dependencies). Subsequent builds should be much faster.

If still slow:
- Make sure you have enough RAM (2GB free minimum)
- Close other heavy applications
- Use SSD instead of HDD if possible
- Check if antivirus is scanning build directory

### Can't connect to emulator

Make sure the emulator is fully booted before running ktroid commands. You'll see "Boot completed" in the emulator window.

---

## Comparison: ktroid vs Android Studio

| What You're Doing | Best Tool | Why |
|-------------------|-----------|-----|
| Designing UI layouts | Android Studio | Visual layout editor is hard to beat |
| Writing Kotlin/Java code | Either | Use your favorite editor + ktroid |
| Building and testing | ktroid | Much faster, no IDE overhead |
| Debugging with breakpoints | Android Studio | Superior debugging tools |
| Profiling performance | Android Studio | CPU/memory profilers are excellent |
| Adding dependencies | ktroid | `ktroid dep retrofit` vs clicking through menus |
| Managing permissions | ktroid | One command vs editing XML |
| CI/CD builds | ktroid | Lightweight, scriptable, no GUI needed |
| Working remotely | ktroid | SSH-friendly, no X11 required |
| Quick hotfixes | ktroid | Build + deploy in seconds |
| Learning Android development | Both | AS for visuals, ktroid to see how things work |

**Bottom line:** Use the right tool for the job. ktroid and Android Studio complement each other - you don't have to choose just one.

---

## How ktroid Works

When you run `ktroid build debug`, here's what happens:

1. **Validates environment:** Checks Java, Gradle, SDK are available
2. **Reads configuration:** Loads versions from `config.json`
3. **Generates Gradle wrapper:** If not already present
4. **Runs Gradle build:** `./gradlew assembleDebug`
5. **Reports status:** Shows build time and APK location

It's basically automating what you'd do manually, but with smart defaults and error handling.

### No Magic, Just Convenience

ktroid doesn't replace Gradle or invent a new build system. It uses the standard Android toolchain:
- Standard Gradle build scripts
- Official Android Gradle Plugin
- Regular APK/AAB output

Your projects remain 100% compatible with Android Studio. You can switch between ktroid and AS anytime.

---

## Project Structure

A ktroid project looks like any other Android project:

```
MyApp/
├── app/
│   ├── src/
│   │   ├── main/
│   │   │   ├── kotlin/
│   │   │   │   └── com/example/myapp/
│   │   │   │       └── MainActivity.kt
│   │   │   ├── res/
│   │   │   │   ├── layout/
│   │   │   │   ├── values/
│   │   │   │   └── drawable/
│   │   │   └── AndroidManifest.xml
│   │   └── test/
│   └── build.gradle
├── gradle/
│   └── wrapper/
├── build.gradle
├── settings.gradle
└── signing.properties  # Created by ktroid signing
```

Nothing proprietary. It's standard Android.

---

## Configuration Reference

The `config.json` file controls toolchain versions:

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

**What each field means:**

- `java_version`: Java/JDK version to use
- `agp_version`: Android Gradle Plugin version
- `gradle_version`: Gradle build tool version
- `kotlin_version`: Kotlin compiler version
- `compile_sdk`: SDK version to compile against
- `min_sdk`: Minimum Android version your app supports
- `target_sdk`: Android version your app targets
- `build_tools_version`: Android build tools version

Edit this file to upgrade your toolchain. ktroid will use the new versions next time you build.

---

## Contributing

Found a bug? Have an idea for a feature? Contributions are welcome!

### Reporting Issues

Open an issue on GitHub with:
- What you were trying to do
- What happened instead
- Your OS and Python version
- Output of `ktroid --check`

### Suggesting Features

Before suggesting a feature, ask yourself:
- Does this fit ktroid's philosophy? (fast, simple, terminal-first)
- Would this benefit most users, or just your specific case?
- Can this be done with a simple script instead?

If yes to all three, open an issue describing your idea.

### Contributing Code

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Test thoroughly (try on Linux and macOS if possible)
5. Commit with clear messages: `git commit -m "Add support for XYZ"`
6. Push to your fork: `git push origin feature/amazing-feature`
7. Open a Pull Request

**Code style:**
- Follow PEP 8 for Python code
- Use clear variable names
- Add comments for complex logic
- Keep functions focused and short
- Don't add dependencies unless absolutely necessary

---

## FAQ

**Q: Does ktroid work on Windows?**
A: Yes, but it's more tested on Linux and macOS. Windows users might need WSL for the best experience.

**Q: Can I use ktroid with Java instead of Kotlin?**
A: Yes, though ktroid assumes Kotlin by default. You can modify the generated templates for Java.

**Q: Does ktroid support Jetpack Compose?**
A: Yes, add it like any other dependency: `ktroid dep androidx.compose.ui:ui:1.5.0`

**Q: Can I use ktroid with Flutter or React Native?**
A: No, ktroid is specifically for native Android development with Kotlin/Java.

**Q: Is ktroid production-ready?**
A: Yes, I use it for my own apps in production. But it's a one-person project, so use at your own risk.

**Q: Why Python instead of Kotlin or Rust?**
A: Python is available everywhere, easy to read, and perfect for scripting. No compilation needed.

**Q: Does ktroid collect any data?**
A: No. Zero telemetry, zero analytics. Everything runs locally.

**Q: Can I use ktroid in a company/commercial project?**
A: Yes, it's MIT licensed. Use it however you want.

---

## Changelog

### v1.0.0 (Current Release)

**New Features:**
- Emulator management (list, start, create)
- Install/uninstall APK commands
- Dependency listing and removal
- Permission removal
- Test runner for unit and instrumented tests
- Version bumping (code, name, or both)
- Multi-density icon generation with Pillow

**Improvements:**
- Better error messages
- Fixed Gradle URL mismatch
- Improved icon handling
- More robust device selection

**Bug Fixes:**
- Fixed duplicate code issues
- Corrected configuration handling
- Improved Windows compatibility

### v0.3.0 (Initial Release)

- Project creation and initialization
- Build system (debug, release, bundle)
- Dependency management
- Permission management
- Basic signing support
- Smart logging
- Configuration management

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

TL;DR: Use it for whatever you want, commercial or personal. Just don't blame me if something breaks.

---

## Credits

Built by [apfsource](https://github.com/apfsource) as a side project.

Thanks to:
- The Android Open Source Project for the SDK tools
- Gradle team for the build system
- Everyone who filed issues and suggestions

---

## Final Thoughts

Android Studio is an amazing IDE. But sometimes you just want to build your app quickly without waiting for a 2GB program to start up.

ktroid gives you that option. It's not trying to replace Android Studio - it's just another tool in your toolkit.

If you're the kind of developer who likes working in the terminal, automating repetitive tasks, and understanding what's happening under the hood, give ktroid a try.

And if you have any questions or run into issues, open an issue on GitHub. I'll do my best to help.

Happy coding! ⚡

---

**Made with ❤️ for terminal-loving Android developers**
