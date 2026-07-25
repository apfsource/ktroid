import os
import typer
from rich.prompt import Prompt, Confirm
from ktroid.core.utils import print_info, print_success, print_error, print_warning, find_project_root

def ci_init(provider: str = typer.Option(None, help="CI provider (github, gitlab)")):
    """Initialize CI/CD pipeline configuration."""
    project_root = find_project_root()
    if not project_root:
        print_error("Error: Project root not found. Are you inside an Android project?")
        raise typer.Exit(1)
    os.chdir(project_root)

    if not provider:
        provider = Prompt.ask("Select CI provider", choices=["github", "gitlab"], default="github")

    if provider == "github":
        workflows_dir = ".github/workflows"
        os.makedirs(workflows_dir, exist_ok=True)
        yml_path = os.path.join(workflows_dir, "android.yml")

        if os.path.exists(yml_path):
            if not Confirm.ask(f"{yml_path} already exists. Overwrite?"):
                return

        with open(yml_path, 'w') as f:
            f.write("""name: Android CI

on:
  push:
    branches: [ "main", "master" ]
  pull_request:
    branches: [ "main", "master" ]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: set up JDK 17
      uses: actions/setup-java@v4
      with:
        java-version: '17'
        distribution: 'temurin'
        cache: gradle

    - name: Grant execute permission for gradlew
      run: chmod +x gradlew

    - name: Build with Gradle
      run: ./gradlew build

    - name: Run Tests
      run: ./gradlew test
""")
        print_success(f"GitHub Actions configuration generated at {yml_path}")

    elif provider == "gitlab":
        yml_path = ".gitlab-ci.yml"

        if os.path.exists(yml_path):
            if not Confirm.ask(f"{yml_path} already exists. Overwrite?"):
                return

        with open(yml_path, 'w') as f:
            f.write("""image: eclipse-temurin:17-jdk-jammy

variables:
  GRADLE_OPTS: "-Dorg.gradle.daemon=false"

before_script:
  - chmod +x ./gradlew

stages:
  - build
  - test

build:
  stage: build
  script:
    - ./gradlew assembleDebug
  artifacts:
    paths:
      - app/build/outputs/

test:
  stage: test
  script:
    - ./gradlew test
""")
        print_success(f"GitLab CI configuration generated at {yml_path}")
    else:
        print_error(f"Unknown provider: {provider}")
