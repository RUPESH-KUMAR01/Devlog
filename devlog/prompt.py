from devlog.collector import CommitData, FileDiff


def build_file_prompt(file: FileDiff) -> str:
    """Build a focused prompt for a single file diff."""

    return f"""Analyze this file change from a git commit.

File: {file.path}

Diff:
{file.diff}

Write 2-3 sentences covering what changed and why. Be specific to this exact diff.

Rules:
- Reference actual function names, variables, or logic from the diff
- Do not invent context or use cases not visible in the diff
- No filler phrases ("to improve", "without manual intervention", "in production environments")
- Output plain text only, no markdown, no headers
"""


def build_whole_diff_prompt(commit: CommitData) -> str:
    """Build a single prompt that sends the full commit diff to the LLM."""

    diff_blocks = []

    for file in commit.files:
        diff_blocks.append(f"### {file.path}\n{file.diff}")

    diff_blob = "\n\n".join(diff_blocks) if diff_blocks else "No file diffs were captured."

    return f"""Generate a development journal entry for this git commit from the full diff.

Commit: {commit.message}
Author: {commit.author}
Date: {commit.date}

Full diff:
{diff_blob}

Output the following markdown sections. No preamble, no explanation — just the document.

Rules:
- Be specific to this commit only. Do not generalize or invent context.
- Use the full diff to explain what changed and why.
- If a section has nothing meaningful to say, write a single short sentence saying so.
- No filler phrases ("to improve the code", "in production environments", "without manual intervention").
- Architecture Impact: only write something if system structure actually changed. Otherwise write "No structural changes."
- Potential Problems: be honest. If there are none, write "None identified."

## Summary
2-3 sentences. What changed and why.

## Files Changed
Bullet list. One line per file — what specifically changed in it.

## Why This Change Was Needed
1-3 sentences. The concrete reason this commit exists.

## Concepts Used
Bullet list of specific technical concepts, patterns, or APIs used. Skip obvious ones (e.g. "variables", "functions").

## Architecture Impact
1-3 sentences on structural change, or "No structural changes."

## Potential Problems
Honest bullet list of risks, gaps, or debt. Or "None identified."

## Next Recommended Commit
2-3 concrete next steps that directly follow from this commit.

## Learning Notes
1-3 sentences on what decisions were made and what tradeoffs were accepted.
"""


def build_log_prompt(commit: CommitData, file_summaries: list[tuple[str, str]]) -> str:
    """Build the final structured devlog prompt from per-file summaries.

    file_summaries: list of (file_path, summary_text) tuples
    """

    summaries_block = "\n\n".join(
        f"### {path}\n{summary}" for path, summary in file_summaries
    )

    return f"""Generate a development journal entry for this git commit.

Commit: {commit.message}
Author: {commit.author}
Date: {commit.date}

File summaries:
{summaries_block}

Output the following markdown sections. No preamble, no explanation — just the document.

Rules:
- Be specific to this commit only. Do not generalize or invent context.
- Reference actual names (functions, classes, fields) from the summaries.
- If a section has nothing meaningful to say, write a single short sentence saying so.
- No filler phrases ("to improve the code", "in production environments", "without manual intervention").
- Architecture Impact: only write something if system structure actually changed. Otherwise write "No structural changes."
- Potential Problems: be honest. If there are none, write "None identified."

## Summary
2-3 sentences. What changed and why.

## Files Changed
Bullet list. One line per file — what specifically changed in it.

## Why This Change Was Needed
1-3 sentences. The concrete reason this commit exists.

## Concepts Used
Bullet list of specific technical concepts, patterns, or APIs used. Skip obvious ones (e.g. "variables", "functions").

## Architecture Impact
1-3 sentences on structural change, or "No structural changes."

## Potential Problems
Honest bullet list of risks, gaps, or debt. Or "None identified."

## Next Recommended Commit
2-3 concrete next steps that directly follow from this commit.

## Learning Notes
1-3 sentences on what decisions were made and what tradeoffs were accepted.
"""