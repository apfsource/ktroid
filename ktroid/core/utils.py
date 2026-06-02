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
