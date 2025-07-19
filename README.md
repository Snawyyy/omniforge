# Omni - AI-Powered CLI Co-Developer

Omni is a project-aware, AI-powered command-line tool for rapid code generation and intelligent, AST-based refactoring. It integrates with local (Ollama) and remote (OpenRouter) LLMs to act as a co-developer directly in your terminal.

## Core Features

-   **Project-Aware Context**: Scan entire directories with the `look` command to build a project manifest that the AI uses for context.
-   **Surgical Code Editing**: Use the `edit` command for precise, AST-based changes to single functions or classes, with intelligent handling of new imports.
-   **Architectural Refactoring**: Leverage the `refactor` command to give high-level instructions, letting the AI create and execute a multi-step, multi-file plan to achieve your goal.
-   **Interactive Menus**: Browse and select from hundreds of updated LLM models with a filterable, interactive menu.
-   **Dual Backend Support**: Seamlessly switch between a local Ollama backend and the OpenRouter API.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/<YourUsername>/<YourRepositoryName>.git
    cd <YourRepositoryName>
    ```

2.  **Install dependencies:**
    Omni relies on a few key Python libraries.
    ```bash
    pip install rich requests astor simple-term-menu prompt-toolkit
    ```

## Configuration

Omni requires an API key to communicate with the OpenRouter service.

1.  **Get an OpenRouter API Key**: Visit [OpenRouter.ai](https://openrouter.ai/) to get your free API key.

2.  **Set the Environment Variable**: You must set the API key as an environment variable. Add the following line to your shell's configuration file (e.g., `~/.bashrc`, `~/.zshrc`):
    ```bash
    export OPENROUTER_API_KEY="your_openrouter_api_key_here"
    ```
    Remember to reload your shell (`source ~/.bashrc`) or restart it for the change to take effect.

## Usage

Run Omni in interactive mode by simply executing the script:

```bash
./omni.py
```

### Core Concepts: Architect vs. Surgeon

-   **The Surgeon (`edit`)**: Use `edit` when you know exactly what you want to change in a specific file. It's for precise, targeted modifications.
-   **The Architect (`refactor`)**: Use `refactor` when you have a high-level goal that may affect multiple files. You provide the goal, and the AI creates the plan.

### Command Reference

| Command | Example | Description |
| :--- | :--- | :--- |
| **`look <path>`** | `look .` | Scans a directory to build a project manifest or reads a single file into the AI's context memory. **This is the first step for any project-level work.** |
| **`edit <file> "..."`** | `edit utils.py "add error handling"` | Performs a targeted AI edit on a single function, class, or the entire file. Can be a path relative to the "looked-at" directory. |
| **`refactor "..."`** | `refactor "extract db logic to a new module"` | **(Project-level)** Asks the AI to create and execute a multi-step plan to refactor the code based on your high-level instruction. |
| **`send <prompt>`** | `send what is the capital of nepal` | Sends a generic prompt to the currently selected LLM. |
| **`models [source]`** | `models google` | Opens an interactive menu to select an LLM. Can be filtered by source (e.g., `openai`, `anthropic`). |
| **`backend <name>`** | `backend ollama` | Switches between `openrouter` and `ollama` backends. |
| **`history`** | `history` | Displays the current session's chat and context history. |
| **`memory clear`** | `memory clear` | Clears the AI's context memory. |
| **`run`** | `run` | Executes the last Python code block that was generated or edited. |

### Example Workflow

1.  **Start Omni and scan your project:**
    ```
    > look .
    ```

2.  **Give a high-level refactoring instruction:**
    ```
    > refactor "move the hardcoded api key from main.py into a new config.py and update the code to import it"
    ```

3.  **Review and approve the AI's plan:**
    Omni will show you the steps the AI intends to take (e.g., CREATE `config.py`, MODIFY `main.py`). Type `y` to proceed.

4.  **Review and approve the generated code:**
    Omni will execute the plan and then show you a final `diff` of all the changes. Type `y` to save the changes to your files.

5.  **You're done!** You have just performed a multi-file refactor with a single command.
