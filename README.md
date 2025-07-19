# OmniForge

**Project‑Aware AI CLI for AST‑Precise Edits (“Scalpel”) & Multi‑File Refactors (“Blueprint”).**

> *OmniForge (a.k.a. the "DualForge" engine) helps you **scan**, **understand**, and **reforge** your codebase with local (Ollama) or remote (OpenRouter) LLMs. It is an independent open‑source project not affiliated with other products using the name “Omni.”*

---

## Core Features

* **Project‑Aware Refactoring (`refactor`)**: Provide a high‑level goal (e.g. *“move all DB logic into `db/` and centralize config”*). OmniForge generates & shows a multi‑step plan before touching files.
* **Surgical AST Editing (`edit`)**: Target a single function/class. OmniForge parses the file, locates the node, applies a structural change, and shows you a diff.
* **Context Ingestion (`look`)**: Scan a directory or single file to build a project manifest (paths + hashes + size + language hints) that guides subsequent edits/refactors.
* **Dual Backends**: Seamlessly switch between **`openrouter`** (remote models) and **`ollama`** (local models) via `backend <name>`.
* **Interactive Model Picker (`models`)**: Filter by source/provider and select from an up‑to‑date model list inside the terminal.
* **Session Memory & History**: `history` shows conversation / action log; `memory clear` resets the working context.
* **Safe AST‑Based Transformations**: Reduces syntax breakage vs naive text substitution. New imports / dependencies are auto‑inserted when possible.
* **Dry‑Run Transparency**: Every multi‑file refactor presents (1) a generated plan, (2) per‑file proposed changes, (3) a consolidated diff for confirmation.

---

## Conceptual Modes

| Mode          | Command(s) | Purpose                                              | Analogy              |
| ------------- | ---------- | ---------------------------------------------------- | -------------------- |
| **Survey**    | `look`     | Index project / ingest context                       | Mapping the terrain  |
| **Scalpel**   | `edit`     | Precise single‑file structural change                | Surgery              |
| **Blueprint** | `refactor` | Multi‑file architectural transformation              | Architecture         |
| **Cast**      | `run`      | Execute last generated runnable block (if supported) | Forging the artifact |

You can reference these terms in docs, help screens, or UI banners for clarity.

---

## Installation

> Requires Python 3.10+ and a Unix‑like shell.

```bash
# 1. Clone
git clone https://github.com/Snawyyy/omniforge.git
cd omniforge

# 2. (Optional) Inspect requirements
cat requirements.txt

# 3. Run installer (creates venv + installs deps)
chmod +x install.sh
./install.sh

# 4. Activate environment
source venv/bin/activate

# 5. Run CLI (interactive shell)
./omni        # or: python omni.py
```

If you later package it, expose a script entry point named `omni` while keeping an internal package name like `omniforge` to avoid namespace collisions.

---

## Configuration

Create a `.env` file to supply secrets (e.g. OpenRouter API key).

```bash
cp .env.example .env   # if example exists; otherwise create manually
```

In `.env`:

```dotenv
OPENROUTER_API_KEY="sk-or-..."
```

(Do **not** commit real keys. Ensure `.env` is listed in `.gitignore`.)

Optional future keys can include local model paths, default model name, or feature flags.

---

## Quick Start Workflow

```text
> look .
(Index project: builds manifest)

> refactor "extract hardcoded API URL to config/settings.py and update all imports"
(Shows plan → ask for confirmation)

> edit src/utils.py "add a doctring for calculate_average explaining parameters and return value"
(Shows targeted diff → confirm or abort)

> models openai
(Choose a different model)

> backend ollama
(Switch to local inference)
```

---

## Command Reference

| Command               | Example                                         | Description                                                                 |
| --------------------- | ----------------------------------------------- | --------------------------------------------------------------------------- |
| `look <path>`         | `look .`                                        | Scan directory or file; update project context manifest.                    |
| `edit <file> "instr"` | `edit utils.py "add error handling"`            | AST‑guided targeted modification of a single file element or whole file.    |
| `refactor "goal"`     | `refactor "split monolith api.py into package"` | High‑level multi‑file transformation with plan + diff review.               |
| `send <prompt>`       | `send summarize module layout`                  | Generic prompt to current model with current context summary.               |
| `models [filter]`     | `models google`                                 | Interactive model selector (filter by provider/source).                     |
| `backend <name>`      | `backend ollama`                                | Switch between `openrouter` / `ollama`.                                     |
| `history`             | `history`                                       | Display session interaction log.                                            |
| `memory clear`        | `memory clear`                                  | Clear internal AI context memory (project manifest may persist separately). |
| `run`                 | `run`                                           | Execute the last generated runnable code snippet (if feature implemented).  |
| `help`                | `help`                                          | Show help / usage summary.                                                  |

---

## How It Works (High Level)

1. **Ingestion (`look`)**: Walks the directory (configurable ignore patterns), captures file metadata (path, size, language), optionally caches abbreviated content or hashes.
2. **Prompt Construction**: Merges user instruction + contextual manifest + focused snippets (for `edit`) or diff summaries (for `refactor`).
3. **AST Layer** (Python initially): Parses target file(s); identifies node(s) (function/class) based on name + heuristic similarity; applies transformations guided by model output (structured hints or patch templates) rather than raw blind overwrite.
4. **Plan (Refactor)**: Model proposes steps (CREATE / MODIFY / RENAME / DELETE). User approves. Each step executed & validated; errors surface early.
5. **Diff Presentation**: A unified colorized diff shown; user confirms to write changes.
6. **Safety**: If AST parse fails or patch violates syntax, changes abort (or fallback to text patch with warning).

---

## Roadmap (Indicative)

| Milestone | Features                                                                    |
| --------- | --------------------------------------------------------------------------- |
| 0.1.0     | Core commands (`look`, `edit`, `refactor`, `models`, `backend`, `history`). |
| 0.2.0     | Config file (`omniforge.toml`), ignore patterns, improved diff viewer.      |
| 0.3.0     | Multi-language AST adapters (JS/TS via `tree-sitter`).                      |
| 0.4.0     | Test impact analysis & auto test file generation.                           |
| 0.5.0     | Refactor preview metrics (LOC touched, complexity delta).                   |
| 0.6.0     | Inline security / lint feedback integration.                                |
| 0.7.0     | Partial GUI / TUI dashboard mode.                                           |

(Adjust roadmap as project evolves.)

---

## Developer Notes

* Keep `.env`, virtual environment dirs (`venv/`), caches, large artifacts in `.gitignore`.
* Consider adding a thin `omniforge/` package directory now for future PyPI packaging.
* Implement a pluggable *Model Adapter* layer to abstract provider differences (OpenRouter vs Ollama).
* Logging: Provide `--verbose` or `OMNIFORGE_DEBUG=1` env flag.
* Add a JSONL log of commands & decisions to enable replay or supervised improvements.

---

## Contributing

1. Fork & create a feature branch: `git checkout -b feat/<short-name>`
2. Run and add tests (if/when test harness exists in `tests/`).
3. Ensure style/format (e.g. `ruff`, `black`) passes.
4. Submit pull request with concise description + before/after examples.

Issues / discussions welcome for architecture proposals, AST adapters, or performance improvements.

---

## License

Released under the **MIT License**. See `LICENSE` file for full text.

---

## Name & Trademark Disclaimer

“OmniForge” is an independent open-source tool and not affiliated with The Omni Group or any other third-party products using similar names. If a future naming conflict arises, a soft alias strategy (keeping the `omni` CLI) will preserve user workflows.

---

## Example Session (Illustrative)

```text
$ ./omni
OMNIFORGE 0.1.0  (backend=openrouter | model=anthropic/claude-3)
Type 'help' or 'look .' to begin.

> look .
Indexed 42 files (Python=30, Markdown=5, JSON=7)

> refactor "centralize logging into logging_util.py and update imports"
Plan:
  [1] CREATE logging_util.py
  [2] MODIFY app.py (replace inline log setup)
  [3] MODIFY worker.py (import logging_util)
Proceed? (y/n) y
... (diff preview) ...
Apply changes? (y/n) y
Refactor complete in 3.2s.

> edit worker.py "add retry with exponential backoff to fetch_data"
Parsed worker.py ✓
Applied modification (function: fetch_data)
Diff shown. Accept? (y/n) y
Saved.
```

---

## Philosophy

*The next wave of developer AI goes beyond paste‑in prompts.* OmniForge treats your repository as *structured material*, enabling incremental, auditable, and safer evolution rather than opaque code dumps. By combining **context scanning**, **AST precision**, and **human approval loops**, it aims to become a trustworthy co‑developer rather than an occasionally helpful code generator.

---

## Feedback / Support

Open a GitHub Issue for bugs & feature requests. For conceptual discussions (roadmap, design choices), use Discussions.

---

Happy forging!
