
import os
import sys
import re
import shutil
import typer
from rich.prompt import Confirm
from ktroid.core.utils import print_info, print_success, print_error, print_warning, get_script_dir, find_project_root

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



def dep(name: str = typer.Argument(None, help="Dependency name or shortcut")):
    """Add a dependency."""
    project_root = find_project_root()
    if project_root:
        os.chdir(project_root)

    if not name:
        print_info("Available Shortcuts:")
        for k, v in COMMON_DEPS.items():
            print(f"  {k:<12} -> {v}")
        print("\nUsage:")
        print("  ktroid dep <shortcut>   (e.g., ktroid dep glide)")
        print("  ktroid dep <coord>      (e.g., ktroid dep com.foo:bar:1.2)")
        return

    dep_str = COMMON_DEPS.get(name.lower(), name)
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



def dep_list():
    """List all dependencies."""
    project_root = find_project_root()
    if project_root:
        os.chdir(project_root)

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



def dep_remove(dep_name: str = typer.Argument(..., help="Dependency to remove")):
    """Remove a dependency."""
    project_root = find_project_root()
    if project_root:
        os.chdir(project_root)

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



def perm(name: str = typer.Argument(None, help="Permission to add")):
    """Add a permission to AndroidManifest."""
    project_root = find_project_root()
    if project_root:
        os.chdir(project_root)

    if not name:
        print_info("Common Permissions:")
        for k, v in COMMON_PERMS.items():
            print(f"  {k:<18} -> {v}")
        print("\nUsage: ktroid perm <name>")
        return

    perm_name = COMMON_PERMS.get(name.lower())
    if not perm_name:
         # Assume user knows what they are doing if not in list
         if "." in name:
             perm_name = name
         else:
             print_error(f"Unknown permission shortcut: {name}")
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



def perm_remove(perm_name: str = typer.Argument(..., help="Permission to remove")):
    """Remove a permission."""
    project_root = find_project_root()
    if project_root:
        os.chdir(project_root)
    
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



def logo(path: str = typer.Argument(..., help="Path to logo image")):
    """Change app logo with multiple density support."""
    # Ensure src image is absolute path before chdir
    src_image = os.path.abspath(path)

    project_root = find_project_root()
    if project_root:
        os.chdir(project_root)

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



def string_add(name: str = typer.Argument(..., help="String resource name (e.g., app_name)"),
               value: str = typer.Argument(..., help="Default string value"),
               locale: str = typer.Option(None, "--locale", "-l", help="Locale code (e.g., es, hi) to add to specific strings.xml")):
    """Add a new string resource directly into strings.xml."""
    project_root = find_project_root()
    if project_root:
        os.chdir(project_root)

    res_dir = "app/src/main/res"
    if not os.path.exists(res_dir):
        print_error("Error: Resource directory not found.")
        return

    target_dir = os.path.join(res_dir, f"values-{locale}") if locale else os.path.join(res_dir, "values")
    os.makedirs(target_dir, exist_ok=True)
    strings_file = os.path.join(target_dir, "strings.xml")

    print_info(f"Adding string resource to {strings_file}...")

    if not os.path.exists(strings_file):
        with open(strings_file, "w") as f:
            f.write("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<resources>\n</resources>")

    with open(strings_file, "r") as f:
        content = f.read()

    # Check if string already exists
    if f'name="{name}"' in content:
        print_warning(f"String resource '{name}' already exists in this file.")
        return

    # Insert before closing tag
    new_content = content.replace("</resources>", f'    <string name="{name}">{value}</string>\n</resources>')

    with open(strings_file, "w") as f:
        f.write(new_content)

    print_success(f"String '{name}' added successfully.")


def bump(bump_type: str = typer.Argument("both", help="Bump type (code, name, both)")):
    """Bump version code/name."""
    project_root = find_project_root()
    if project_root:
        os.chdir(project_root)

    build_file = "app/build.gradle"
    
    if not os.path.exists(build_file):
        print_error("app/build.gradle not found.")
        return
    
    with open(build_file, 'r') as f:
        content = f.read()
    
    bump_type = bump_type
    
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


