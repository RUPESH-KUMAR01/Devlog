# devlog-cli

> A git-powered development journal. Every commit becomes a structured learning log — automatically.

Instead of losing context between commits, `devlog-cli` uses an LLM to analyze your diff and generate a markdown log covering what was built, why, what you learned, and what to do next.

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
Ollama or Groq  (auto-selected from config)
    ↓
docs/devlogs/NNN-slug.md
```

By default, devlog uses local Ollama. If a Groq API key is configured, devlog automatically switches to Groq Cloud inference.

---

## Installation

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) running locally
- A pulled model, e.g. `ollama pull llama3`
- Optional: a Groq API key for cloud inference

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
[provider]
mode = "auto" # auto, local, ollama, cloud, or groq

[ollama]
host = "http://localhost:11434"
model = "llama3"

[groq]
api_key = ""
api_key_env = "GROQ_API_KEY"
base_url = "https://api.groq.com/openai/v1"
model = "llama-3.3-70b-versatile"

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

To use Groq Cloud, either set `GROQ_API_KEY` in your shell or put a key in config:

```toml
[groq]
api_key = "gsk_..."
```

With `provider.mode = "auto"`, devlog uses Groq when an API key is available and Ollama when it is not.

---

## CLI reference

```
devlog                  Generate a log from the entire diff in one LLM pass
devlog --mode file      Generate a log using per-file summaries instead
devlog generate --mode file Same behavior, using the explicit subcommand
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
| Groq Cloud | ✅ Supported | Auto-selected when a Groq API key is configured. |
| Anthropic | 🔜 Planned | Future cloud provider. |
| OpenAI | 🔜 Planned | Future cloud provider. |
| Gemini | 🔜 Planned | Future cloud provider. |

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
│   ├── ai.py           # Ollama and Groq clients (provider interface)
│   ├── writer.py       # numbers, slugifies, writes .md files
│   └── config.py       # loads and merges global + project config
├── pyproject.toml
├── LICENSE
└── README.md
```

---

## Why local by default

- Your diffs contain private business logic. They shouldn't leave your machine by default.
- Ollama is free, runs offline, and is fast enough for this use case.
- Groq Cloud is opt-in and only selected when a key is configured.

---


```bash
git clone https://github.com/RUPESH-KUMAR01/Devlog
cd devlog-cli
pip install -e ".[dev]"
```
