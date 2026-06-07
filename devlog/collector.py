from dataclasses import dataclass
import subprocess


@dataclass
class FileDiff:
    path: str
    diff: str


@dataclass
class CommitData:
    hash: str
    short_hash: str
    author: str
    email: str
    date: str
    message: str
    files: list[FileDiff]


def collect_devlog() -> CommitData:
    """Collect metadata and per-file diffs for HEAD."""

    result = subprocess.run(
        [
            "git",
            "show",
            "HEAD",
            "--pretty=format:%H%n%an%n%ae%n%aI%n%s",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError("Not a git repository or no commits found.")

    output = result.stdout

    # Separate commit metadata from diff section
    if "diff --git" in output:
        meta, diff_blob = output.split("diff --git", 1)
        diff_blob = "diff --git" + diff_blob
    else:
        meta, diff_blob = output, ""

    lines = meta.strip().splitlines()

    commit_hash = lines[0]
    author = lines[1]
    email = lines[2]
    date = lines[3]
    message = lines[4]

    files: list[FileDiff] = []

    if diff_blob:
        sections = diff_blob.split("diff --git ")

        for section in sections:
            if not section.strip():
                continue

            full_diff = "diff --git " + section

            first_line = section.splitlines()[0]

            # Example:
            # a/devlog/collector.py b/devlog/collector.py
            parts = first_line.split()

            if len(parts) >= 2:
                path = parts[-1].removeprefix("b/")
            else:
                path = "unknown"

            files.append(
                FileDiff(
                    path=path,
                    diff=full_diff,
                )
            )

    data = CommitData(
        hash=commit_hash,
        short_hash=commit_hash[:7],
        author=author,
        email=email,
        date=date,
        message=message,
        files=files,
    )
    return data