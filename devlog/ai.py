import requests

from devlog.config import Config
from devlog.collector import CommitData
from devlog.prompt import build_file_prompt, build_log_prompt, build_whole_diff_prompt




class OllamaError(Exception):
    pass


def _call_ollama(prompt: str, config: Config) -> str:
    """Send a prompt to Ollama and return the response text."""

    print(f"\n→ Calling Ollama ({config.ollama_model})...")
    print(f"→ Prompt length: {len(prompt):,} chars")

    try:
        response = requests.post(
            f"{config.ollama_host}/api/generate",
            json={
                "model": config.ollama_model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=120,
        )

        print(f"→ HTTP Status: {response.status_code}")

        if response.status_code != 200:
            print("→ Response body:")
            print(response.text)

        response.raise_for_status()

    except requests.ConnectionError:
        raise OllamaError(
            f"Could not connect to Ollama at {config.ollama_host}. Is it running?"
        )
    except requests.Timeout:
        raise OllamaError("Ollama request timed out.")
    except requests.HTTPError as e:
        raise OllamaError(f"Ollama returned an error: {e}")

    try:
        data = response.json()
    except Exception:
        raise OllamaError(
            f"Could not parse Ollama response as JSON:\n{response.text}"
        )

    if "response" not in data:
        raise OllamaError(
            f"Unexpected Ollama response shape:\n{data}"
        )

    print("✓ Ollama response received")

    return data["response"].strip()


def _summarize_file(path: str, diff: str, config: Config) -> tuple[str, str]:
    """Run pass 1: summarize a single file diff."""

    from devlog.collector import FileDiff

    print(f"\n📄 Summarizing: {path}")

    file = FileDiff(
        path=path,
        diff=diff,
    )

    prompt = build_file_prompt(file)

    summary = _call_ollama(prompt, config)

    print(f"✓ Finished: {path}")

    return path, summary


def _generate_from_file_summaries(commit: CommitData, config: Config) -> str:
    """
    Pass 1:
        Summarize each file independently.

    Pass 2:
        Generate final devlog from file summaries.
    """

    print(f"\nCommit: {commit.short_hash}")
    print(f"Message: {commit.message}")
    print(f"Files: {len(commit.files)}")

    file_summaries: list[tuple[str, str]] = []

    if not commit.files:
        print("No changed files found.")
    else:
        for index, f in enumerate(commit.files, start=1):
            print(
                f"\n[{index}/{len(commit.files)}] Processing {f.path}"
            )

            path, summary = _summarize_file(
                f.path,
                f.diff,
                config
            )

            file_summaries.append((path, summary))

    print("\n📝 Building final devlog prompt...")

    log_prompt = build_log_prompt(
        commit,
        file_summaries,
    )

    print("🤖 Generating final devlog...")

    devlog_markdown = _call_ollama(log_prompt, config)

    print("✅ Devlog generated")

    return devlog_markdown


def _generate_from_whole_diff(commit: CommitData, config: Config) -> str:
    """Generate a devlog by sending the full diff to the LLM in one prompt."""

    print("\n📝 Building whole-diff prompt...")

    log_prompt = build_whole_diff_prompt(commit)

    print("🤖 Generating devlog from full diff...")

    devlog_markdown = _call_ollama(log_prompt, config)

    print("✅ Devlog generated")

    return devlog_markdown


def generate_devlog(commit: CommitData, config: Config, mode: str = "whole-diff") -> str:
    """Generate a devlog using the requested summarization mode."""

    if mode == "file":
        return _generate_from_file_summaries(commit, config)

    if mode == "whole-diff":
        return _generate_from_whole_diff(commit, config)

    return _generate_from_whole_diff(commit, config)