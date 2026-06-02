# ktroid (ktd) - Future Roadmap 🚀

This document outlines the planned features and improvements for upcoming versions to make `ktroid` a world-class, industry-standard CLI tool for Android development.

## 🔜 Next Release (v2.1.0)
- **Dynamic Config Updater (`ktd update-config`)**: Automatically fetch and update the latest versions of Kotlin, Gradle, AGP, and Android SDK from official APIs.
- **Auto-Signing (`ktd signing init`)**: Automatically generate secure release keystores and configure them in `signing.properties` without manual XML/Gradle editing.

## 🌟 Short-term Goals (v2.2.0 - v2.4.0)
- **Project Templates**: Support for generating specific architectures (e.g., `ktd create MyApp --template compose`, `--template mvvm`).
- **Interactive UI Mode**: Add a full terminal wizard (using `rich.prompt`) to guide beginners through creating apps.
- **Dependency Search (`ktd dep-search <name>`)**: Search Maven Central directly from the terminal to find the exact dependency string without opening a browser.
- **Logcat Colorizer**: Enhance `ktd logs` with beautiful, color-coded, and tag-filtered output for easier debugging.

## 🚀 Long-term Vision (v3.0.0+)
- **CI/CD Integration**: One-command GitHub Actions setup (`ktd ci setup`) for automated building and testing.
- **Plugin System**: Allow developers to write custom Python/Bash plugins that hook into `ktd build` and `ktd run` lifecycles.
- **Multi-module Support**: Commands to easily generate and manage multi-module Android architectures.
- **Firebase/Supabase Integration**: Add BaaS (Backend as a Service) configuration automatically to the project.
