from dataclasses import dataclass
from pathlib import Path
try:
    import tomllib # type: ignore
except ImportError:
    import tomli as tomllib  # type: ignore


CONFIG_DIR = Path.home() / ".config" / "devlog"
CONFIG_FILE = CONFIG_DIR / "config.toml"


@dataclass
class Config:
    ollama_host: str
    ollama_model: str
    output_dir: str
    include_diff: bool


DEFAULT_CONFIG = """
[ollama]
host = "http://localhost:11434"
model = "qwen3:4b"

[output]
dir = "docs/devlogs"

[log]
include_diff = false
""".strip()


def ensure_config_exists() -> None:
    """Create default config if missing."""

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(DEFAULT_CONFIG)



def load_project_config() -> dict:
    """Load .devlog.toml from current working directory if present."""
    project_config = Path.cwd() / ".devlog.toml"
    if project_config.exists():
        with open(project_config, "rb") as f:
            return tomllib.load(f)
    return {}


def load_config() -> Config:
    ensure_config_exists()

    with open(CONFIG_FILE, "rb") as f:
        data = tomllib.load(f)

    # project config overrides global
    project = load_project_config()
    if "ollama" in project:
        data["ollama"].update(project["ollama"])
    if "output" in project:
        data["output"].update(project["output"])
    if "log" in project:
        data["log"].update(project["log"])

    return Config(
        ollama_host=data["ollama"]["host"],
        ollama_model=data["ollama"]["model"],
        output_dir=data["output"]["dir"],
        include_diff=data["log"]["include_diff"],
    )