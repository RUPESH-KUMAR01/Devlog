from dataclasses import dataclass
import subprocess

@dataclass
class CommitData:
    hash: str
    short_hash: str
    author: str
    email: str
    date: str
    message: str
    diff: str

def collect_devlog() -> CommitData:
    """Collect a devlog for the latest commit."""

    result = subprocess.run(
        ["git", "show", "HEAD", "--pretty=format:%H%n%an%n%ae%n%aI%n%s"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError("Not a git repository or no commits found.")
    
    result = result.stdout
    # split metadata from diff
    if "diff --git" in result:
        meta, diff = result.split("diff --git", 1)
        diff = "diff --git" + diff
    else:
        meta, diff = result, ""

    lines = meta.strip().splitlines()
    data = CommitData(
        hash=lines[0],
        short_hash=lines[0][:7],
        author=lines[1],
        email=lines[2],
        date=lines[3],
        message=lines[4],
        diff=diff,
    )
    return data