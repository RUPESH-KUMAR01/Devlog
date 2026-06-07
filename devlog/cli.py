import shutil

import typer

from devlog.ai import generate_devlog
from devlog.collector import collect_devlog
from devlog.config import Config, ConfigError, load_config
from devlog.writer import get_git_root, write_devlog

app = typer.Typer(
    help="A git-powered development journal.",
    add_completion=False,
)


def _load_config_or_exit() -> Config:
    try:
        return load_config()
    except ConfigError as e:
        typer.echo(f"✗ {e}", err=True)
        raise typer.Exit(1) from e


def _generate_log(mode: str) -> None:
    config = _load_config_or_exit()
    commit = collect_devlog()
    markdown = generate_devlog(commit, config, mode=mode)
    path = write_devlog(commit, markdown, config)
    typer.echo(f"✔ devlog written → {path}")

def build_hook() -> str:
    """Build a git hook that calls the currently installed devlog executable."""

    devlog_path = shutil.which("devlog")

    if not devlog_path:
        raise RuntimeError(
            "Could not find 'devlog' executable in PATH."
        )

    return f"""#!/bin/sh
"{devlog_path}"
"""
 
@app.command()
def install():
    """Install the git post-commit hook."""

    try:
        git_root = get_git_root()
    except RuntimeError as e:
        typer.echo(f"✗ {e}", err=True)
        raise typer.Exit(1)

    hook_path = git_root / ".git" / "hooks" / "post-commit"

    if hook_path.exists():
        contents = hook_path.read_text()

        if "devlog" not in contents:
            typer.echo(
                "✗ Existing post-commit hook is not managed by devlog.",
                err=True,
            )
            raise typer.Exit(1)

        typer.echo(
            f"✗ Devlog hook already installed at {hook_path}",
            err=True,
        )
        raise typer.Exit(1)

    hook_path.write_text(build_hook())
    hook_path.chmod(0o755)

    typer.echo(f"✔ post-commit hook installed → {hook_path}")
 
@app.command()
def uninstall():
    """Remove the git post-commit hook."""
 
    try:
        git_root = get_git_root()
    except RuntimeError as e:
        typer.echo(f"✗ {e}", err=True)
        raise typer.Exit(1)
 
    hook_path = git_root / ".git" / "hooks" / "post-commit"
 
    if not hook_path.exists():
        typer.echo("✗ No post-commit hook found.", err=True)
        raise typer.Exit(1)
 
    if "devlog" not in hook_path.read_text():
        typer.echo("✗ Hook exists but wasn't installed by devlog. Aborting.", err=True)
        raise typer.Exit(1)
 
    hook_path.unlink()
    typer.echo("✔ post-commit hook removed.")
 
 
@app.command(name="config")
def show_config():
    """Show resolved configuration."""
 
    config = _load_config_or_exit()
    typer.echo(f"provider      {config.provider}")
    typer.echo(f"provider_mode {config.provider_mode}")
    typer.echo(f"ollama_host   {config.ollama_host}")
    typer.echo(f"ollama_model  {config.ollama_model}")
    typer.echo(f"groq_model    {config.groq_model}")
    typer.echo(f"groq_api_key  {'configured' if config.groq_api_key else 'missing'}")
    typer.echo(f"output_dir    {config.output_dir}")
    typer.echo(f"include_diff  {config.include_diff}")
 
 
@app.command(name="list")
def list_logs():
    """List generated devlogs."""
 
    try:
        git_root = get_git_root()
    except RuntimeError as e:
        typer.echo(f"✗ {e}", err=True)
        raise typer.Exit(1)
 
    config = _load_config_or_exit()
    output_dir = git_root / config.output_dir
 
    if not output_dir.exists() or not (logs := sorted(output_dir.glob("*.md"))):
        typer.echo("No devlogs found.")
        return
 
    for log in logs:
        typer.echo(f"  {log.name}")
 
 
@app.command()
def show(log_number: int = typer.Argument(..., help="Log number, e.g. 4")):
    """Show a specific devlog."""
 
    try:
        git_root = get_git_root()
    except RuntimeError as e:
        typer.echo(f"✗ {e}", err=True)
        raise typer.Exit(1)
 
    config = _load_config_or_exit()
    output_dir = git_root / config.output_dir
    matches = list(output_dir.glob(f"{log_number:03d}-*.md"))
 
    if not matches:
        typer.echo(f"✗ No devlog found for number {log_number:03d}.", err=True)
        raise typer.Exit(1)
 
    typer.echo(matches[0].read_text())
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
