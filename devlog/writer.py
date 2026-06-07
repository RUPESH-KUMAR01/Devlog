import re
import subprocess
from pathlib import Path

from devlog.collector import CommitData
from devlog.config import Config


def get_git_root() -> Path:
    """Find the root of the current git repository."""

    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError("Not a git repository.")

    return Path(result.stdout.strip())


def slugify(text: str) -> str:
    """Convert commit message to a filename-safe slug."""

    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = text.strip("-")
    return text


def next_log_number(output_dir: Path) -> int:
    """Return the next log number based on existing files."""

    existing = list(output_dir.glob("*.md"))
    return len(existing) + 1


def build_header(commit: CommitData, number: int) -> str:
    """Build the header block prepended before LLM output."""

    date = commit.date[:10]  # ISO date → YYYY-MM-DD

    return f"""# Commit {number:03d}

Date: {date}
Commit: {commit.short_hash}
Author: {commit.author}

"""


def write_devlog(commit: CommitData, markdown: str, config: Config) -> Path:
    """Write the devlog file and return its path."""

    git_root = get_git_root()
    output_dir = git_root / config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # If a log for this commit already exists, overwrite it instead of
    # creating a new numbered file. This prevents generating multiple
    # files for the same commit when the generator is invoked repeatedly.
    def _find_existing_by_short_hash(short_hash: str) -> Path | None:
        for p in output_dir.glob("*.md"):
            try:
                txt = p.read_text()
            except Exception:
                continue

            if f"Commit: {short_hash}" in txt:
                return p

        return None

    existing = _find_existing_by_short_hash(commit.short_hash)

    if existing:
        # Preserve original filename/number; just update contents.
        # Header numbering should reflect the existing file's number, so
        # attempt to extract it from the filename; fall back to 0.
        try:
            existing_name = existing.name
            number = int(existing_name.split("-", 1)[0])
        except Exception:
            number = 0

        header = build_header(commit, number)
        existing.write_text(header + markdown)
        return existing

    # No existing log found — create a new numbered file.
    number = next_log_number(output_dir)
    slug = slugify(commit.message)
    filename = f"{number:03d}-{slug}.md"
    filepath = output_dir / filename

    header = build_header(commit, number)
    filepath.write_text(header + markdown)

    return filepath