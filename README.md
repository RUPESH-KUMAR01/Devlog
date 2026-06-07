# devlog-cli

> A git-powered development journal. Every commit becomes a structured learning log — automatically.

Instead of losing context between commits, `devlog-cli` uses a local LLM to analyze your diff and generate a markdown log covering what was built, why, what you learned, and what to do next.

```
$ git commit -m "add user verification"

[main 4a3f92c] add user verification
 3 files changed, 47 insertions(+), 2 deletions(-)

✔ devlog written → docs/devlogs/004-add-user-verification.md
```

---

## What it generates

```markdown
# Commit 004

Date: 2026-06-07

## Summary
Added emailVerified and phoneVerified fields to the User entity.
Introduced isFullyVerified() helper and updated the admin bootstrap flow.

## Files Changed
- src/models/user.py
- src/services/admin.py
- tests/test_user.py

## Why This Change Was Needed
Account verification needs to be tracked independently from roles.
Event registration will gate on this state in a future commit.

## Concepts Used
- Entity state modeling
- Separation of verification vs. authorization concerns

## Architecture Impact
User entity now owns verification state. A future VerificationService
will own the logic for transitioning that state.

## Potential Problems
- No VerificationService yet — the flag can be set but not triggered automatically.
- Admin bootstrap bypasses verification; document this assumption.

## Next Recommended Commit
- Implement VerificationService
- Extract login/register logic out of AuthResource

## Learning Notes
Verification and authorization are different concerns. Mixing them
leads to bloated User models and unclear permission logic.
```

---

## How it works

```
git commit
    ↓
.git/hooks/post-commit
    ↓
devlog          ← this tool
    ↓
git show HEAD   (diff collector)
    ↓
Ollama          (local LLM, no API key needed)
    ↓
docs/devlogs/NNN-slug.md
```

No cloud. No API keys. No data leaves your machine.

---

## Installation

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) running locally
- A pulled model, e.g. `ollama pull llama3`

### Install devlog-cli

```bash
git clone https://github.com/yourusername/devlog-cli
cd devlog-cli
pip install -e .
```

This registers the `devlog` command globally.

### Enable in a repo

Inside any git repository:

```bash
devlog install
```

This writes a `post-commit` hook into `.git/hooks/`. From this point on, every `git commit` in that repo automatically generates a log.

---

## Configuration

On first run, `devlog` creates a config file at `~/.config/devlog/config.toml`:

```toml
[ollama]
host = "http://localhost:11434"
model = "llama3"

[output]
dir = "docs/devlogs"

[log]
include_diff = false   # set true to append raw diff to the log
```

Override the model per-project by adding a `.devlog.toml` at your repo root:

```toml
[ollama]
model = "mistral"
```

Project-level config takes precedence over global config.

---

## CLI reference

```
devlog                  Generate a log for HEAD (run manually)
devlog install          Install post-commit hook in current repo
devlog uninstall        Remove the hook from current repo
devlog config           Print resolved config (global + project merged)
devlog list             List all logs in docs/devlogs/
devlog show 004         Print a specific log
```

---

## Log file naming

Logs are numbered sequentially and slugified from the commit message:

```
docs/devlogs/
├── 001-initial-project-setup.md
├── 002-add-jwt-authentication.md
├── 003-user-entity-and-dao.md
└── 004-add-user-verification.md
```

The number is based on how many logs already exist in the output directory, so the sequence is always consistent regardless of branch.

---

## Supported LLM providers

| Provider | Status | Notes |
|----------|--------|-------|
| Ollama (local) | ✅ Supported | Default. No API key needed. |
| Anthropic | 🔜 Planned | Set `provider = "anthropic"` in config |
| OpenAI | 🔜 Planned | Set `provider = "openai"` in config |
| Gemini | 🔜 Planned | Set `provider = "gemini"` in config |

The provider interface is designed so adding a new one means implementing a single function:

```python
def summarize(diff: str, config: Config) -> str:
    ...
```

---

## Project structure

```
devlog-cli/
├── devlog/
│   ├── __init__.py
│   ├── cli.py          # entry point, subcommands
│   ├── collector.py    # runs git show HEAD, parses output
│   ├── prompt.py       # builds the LLM prompt from diff
│   ├── ai.py           # Ollama client (provider interface)
│   ├── writer.py       # numbers, slugifies, writes .md files
│   └── config.py       # loads and merges global + project config
├── pyproject.toml
├── LICENSE
└── README.md
```

---

## Why local LLM

- Your diffs contain private business logic. They shouldn't leave your machine by default.
- Ollama is free, runs offline, and is fast enough for this use case.
- Cloud providers are opt-in — you choose when to enable them.

---


```bash
git clone https://github.com/RUPESH-KUMAR01/Devlog
cd devlog-cli
pip install -e ".[dev]"
```
