import typer

from devlog.ai import generate_devlog
from devlog.collector import collect_devlog
from devlog.config import load_config
from devlog.writer import write_devlog

app = typer.Typer(
    help="A git-powered development journal.",
    add_completion=False,
)


def _generate_log(mode: str) -> None:
    config = load_config()
    commit = collect_devlog()
    markdown = generate_devlog(commit, config, mode=mode)
    path = write_devlog(commit, markdown, config)
    typer.echo(f"✔ devlog written → {path}")


@app.command()
def install():
    """Install the git post-commit hook."""
    pass


@app.command()
def uninstall():
    """Remove the git post-commit hook."""
    pass


@app.command(name="list")
def list_logs():
    """List generated devlogs."""
    pass

@app.command(name="config")
def show_config():
    """Show resolved configuration."""
    pass

@app.command()
def show(log_number: int = typer.Argument(..., help="Log number, e.g. 4")):
    """Show a specific devlog."""
    pass

@app.command()
def generate(
    mode: str = typer.Option(
        "whole-diff",
        "--mode",
        help="Summarization mode: whole-diff or file.",
        show_default=True,
    ),
):
    """Generate a devlog for the latest commit."""
    _generate_log(mode)

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context, mode: str = typer.Option("whole-diff", "--mode")):
    if ctx.invoked_subcommand is None:
        # no subcommand → generate log for HEAD
        _generate_log(mode)


if __name__ == "__main__":
    app()