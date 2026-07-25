import typer
from rich.console import Console

# Import command functions
from ktroid.commands.project import create, init, info
from ktroid.commands.build import build, clean, signing, run, test, lint
from ktroid.commands.device import logs, emulator, install, uninstall, screen, connect_wifi, db_pull
from ktroid.commands.packages import dep, dep_list, dep_remove, perm, perm_remove, logo, bump, string_add
from ktroid.commands.setup import setup, config, check, update_config
from ktroid.commands.ci import ci_init
from ktroid import __version__

console = Console()

app = typer.Typer(
    name="ktroid",
    help="⚡ Build, run and test native Android apps entirely from the terminal.",
    epilog="""
[bold yellow]🚀 Quick Start:[/bold yellow] 
To create a fresh project, run:
  [bold cyan]ktd create MyApp com.example.myapp[/bold cyan]

[bold green]🌐 Documentation & Help:[/bold green] 
Visit [bold red][link=https://ktd.acharyaml.com]https://ktd.acharyaml.com[/link][/bold red] for full guides.
""",
    add_completion=False,
    rich_markup_mode="rich"
)

# 📦 Project Commands
app.command(name="create", rich_help_panel="📦 Project Commands")(create)
app.command(name="init", rich_help_panel="📦 Project Commands")(init)
app.command(name="info", rich_help_panel="📦 Project Commands")(info)

# 🔨 Build Commands
app.command(name="build", rich_help_panel="🔨 Build Commands")(build)
app.command(name="clean", rich_help_panel="🔨 Build Commands")(clean)
app.command(name="signing", rich_help_panel="🔨 Build Commands")(signing)
app.command(name="run", rich_help_panel="🔨 Build Commands")(run)
app.command(name="test", rich_help_panel="🔨 Build Commands")(test)
app.command(name="lint", rich_help_panel="🔨 Build Commands")(lint)

# 📱 Device Commands
app.command(name="logs", rich_help_panel="📱 Device Commands")(logs)
app.command(name="emulator", rich_help_panel="📱 Device Commands")(emulator)
app.command(name="install", rich_help_panel="📱 Device Commands")(install)
app.command(name="uninstall", rich_help_panel="📱 Device Commands")(uninstall)
app.command(name="screen", rich_help_panel="📱 Device Commands")(screen)
app.command(name="connect-wifi", rich_help_panel="📱 Device Commands")(connect_wifi)
app.command(name="db-pull", rich_help_panel="📱 Device Commands")(db_pull)

# 🧩 Package Commands
app.command(name="dep", rich_help_panel="🧩 Package Commands")(dep)
app.command(name="dep-list", rich_help_panel="🧩 Package Commands")(dep_list)
app.command(name="dep-remove", rich_help_panel="🧩 Package Commands")(dep_remove)
app.command(name="perm", rich_help_panel="🧩 Package Commands")(perm)
app.command(name="perm-remove", rich_help_panel="🧩 Package Commands")(perm_remove)
app.command(name="logo", rich_help_panel="🧩 Package Commands")(logo)
app.command(name="bump", rich_help_panel="🧩 Package Commands")(bump)
app.command(name="string-add", rich_help_panel="🧩 Package Commands")(string_add)

# ⚙️ CI/CD Commands
app.command(name="ci-init", rich_help_panel="⚙️ CI/CD Commands")(ci_init)

# ⚙️ Setup Commands
app.command(name="setup", rich_help_panel="⚙️ Setup Commands")(setup)
app.command(name="config", rich_help_panel="⚙️ Setup Commands")(config)
app.command(name="check", rich_help_panel="⚙️ Setup Commands")(check)
app.command(name="update-config", rich_help_panel="⚙️ Setup Commands")(update_config)

@app.command(name="version", rich_help_panel="⚙️ Setup Commands")
def show_version():
    """Show the application's version."""
    console.print(f"[bold cyan]ktroid[/bold cyan] (ktd) version [bold green]{__version__}[/bold green]")

def version_callback(value: bool):
    if value:
        console.print(f"[bold cyan]ktroid[/bold cyan] (ktd) version [bold green]{__version__}[/bold green]")
        raise typer.Exit()

@app.callback()
def main_callback(
    version: bool = typer.Option(
        None, "--version", "-v", 
        callback=version_callback, 
        is_eager=True, 
        help="Show the version and exit."
    )
):
    pass

def main():
    app()

if __name__ == "__main__":
    main()
