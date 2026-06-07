from dataclasses import dataclass
import os
from pathlib import Path

try:
    import tomllib  # type: ignore
except ImportError:
    import tomli as tomllib  # type: ignore


CONFIG_DIR = Path.home() / ".config" / "devlog"
CONFIG_FILE = CONFIG_DIR / "config.toml"


@dataclass
class Config:
    provider: str
    provider_mode: str
    ollama_host: str
    ollama_model: str
    groq_api_key: str | None
    groq_base_url: str
    groq_model: str
    output_dir: str
    include_diff: bool


DEFAULT_CONFIG = """
[provider]
mode = "auto"

[ollama]
host = "http://localhost:11434"
model = "qwen3:4b"

[groq]
api_key = ""
api_key_env = "GROQ_API_KEY"
base_url = "https://api.groq.com/openai/v1"
model = "llama-3.3-70b-versatile"

[output]
dir = "docs/devlogs"

[log]
include_diff = false
""".strip()


def _default_config_data() -> dict:
    return tomllib.loads(DEFAULT_CONFIG)


def _merge_config(base: dict, override: dict) -> dict:
    """Recursively merge TOML config data into base."""

    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _merge_config(base[key], value)
        else:
            base[key] = value

    return base


def _resolve_groq_api_key(groq: dict) -> str | None:
    api_key = str(groq.get("api_key") or "").strip()

    if api_key.startswith("$"):
        return os.getenv(api_key[1:]) or None

    if api_key:
        return api_key

    api_key_env = str(groq.get("api_key_env") or "").strip()
    if api_key_env:
        return os.getenv(api_key_env) or None

    return None


def _resolve_provider(mode: str, groq_api_key: str | None) -> str:
    normalized = mode.strip().lower()

    if normalized == "auto":
        return "groq" if groq_api_key else "ollama"

    if normalized in {"local", "ollama"}:
        return "ollama"

    if normalized in {"cloud", "groq"}:
        if not groq_api_key:
            raise ValueError(
                "Groq cloud inference is selected, but no Groq API key is configured."
            )
        return "groq"

    raise ValueError(
        "Invalid provider mode. Use auto, local, ollama, cloud, or groq."
    )


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

    data = _default_config_data()

    with open(CONFIG_FILE, "rb") as f:
        _merge_config(data, tomllib.load(f))

    # project config overrides global
    project = load_project_config()
    _merge_config(data, project)

    provider_mode = data["provider"]["mode"]
    groq_api_key = _resolve_groq_api_key(data["groq"])

    return Config(
        provider=_resolve_provider(provider_mode, groq_api_key),
        provider_mode=provider_mode,
        ollama_host=data["ollama"]["host"],
        ollama_model=data["ollama"]["model"],
        groq_api_key=groq_api_key,
        groq_base_url=data["groq"]["base_url"],
        groq_model=data["groq"]["model"],
        output_dir=data["output"]["dir"],
        include_diff=data["log"]["include_diff"],
    )
