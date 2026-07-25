
import os
import sys
import shutil
import typer
from rich.prompt import Prompt, Confirm
from ktroid.core.utils import print_info, print_success, print_error, print_warning, run_command, get_script_dir
from ktroid.core.config import CONFIG, get_template_path

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
    render_template('ktroid.md', os.path.join(project_dir, 'ktroid.md'))
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



def create(project_name: str, package_name: str = None):
    """Create a new Android project."""
    if not package_name:
        package_name = f"com.example.{project_name.lower()}"
        
    project_dir = os.path.join(os.getcwd(), project_name)

    if os.path.exists(project_dir):
        print_error(f"Error: Directory '{project_name}' already exists.")
        raise typer.Exit(1)

    print_info(f"Creating project '{project_name}' at {project_dir}...")
    print_info(f"Package: {package_name}")
    
    os.makedirs(project_dir)
    generate_project_structure(project_dir, project_name, package_name)

def init():
    """Initialize a project in the current directory."""
    cwd = os.getcwd()
    default_name = os.path.basename(cwd)
    
    project_name = Prompt.ask("Project Name", default=default_name).strip() or default_name
    default_package = f"com.example.{project_name.lower()}"
    package_name = Prompt.ask("Package Name", default=default_package).strip() or default_package
    
    print_info(f"Initializing project '{project_name}' in current directory...")
    
    if os.listdir(cwd):
        print_warning("Warning: Current directory is NOT empty.")
        if not Confirm.ask("Continue anyway?"):
            print_info("Aborting.")
            raise typer.Exit()

    generate_project_structure(cwd, project_name, package_name)

from ktroid.core.utils import find_project_root

def info():
    """Extract info from build.gradle."""
    project_root = find_project_root()
    if project_root:
        os.chdir(project_root)

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

