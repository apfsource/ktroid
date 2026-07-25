import os
import subprocess
import shutil
from rich.console import Console

console = Console()

def print_success(msg):
    console.print(f"[bold green]{msg}[/bold green]")

def print_error(msg):
    console.print(f"[bold red]{msg}[/bold red]")

def print_warning(msg):
    console.print(f"[bold yellow]{msg}[/bold yellow]")

def print_info(msg):
    console.print(f"[bold cyan]{msg}[/bold cyan]")

def get_script_dir():
    # Returns the root of the ktroid package
    return os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

def find_project_root(current_dir=None):
    """
    Climbs the directory tree to find the project root containing 'gradlew' or 'app/build.gradle'.
    Returns the project root path if found, otherwise None.
    """
    if current_dir is None:
        current_dir = os.getcwd()

    original_dir = current_dir
    while True:
        if os.path.exists(os.path.join(current_dir, "gradlew")) or \
           os.path.exists(os.path.join(current_dir, "app", "build.gradle")):
            return current_dir

        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            # Reached root of the filesystem
            return None
        current_dir = parent_dir

def run_command(command, cwd=None, show_output=True):
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
