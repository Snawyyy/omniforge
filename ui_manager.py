from typing import List
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.status import Status
from rich import box
from contextlib import contextmanager
try:
    from prompt_toolkit import prompt
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.history import InMemoryHistory
    from prompt_toolkit.styles import Style
except ImportError:
    print("[yellow]prompt_toolkit not installed. Falling back to basic input.[/]")
    prompt = input  # Fallback

class UIManager:
    """Manages interactive text-based UI with rich for display and prompt_toolkit for input.
    
    Enhanced with visual indicators for better UX: spinners for feedback, color-coding for clarity,
    status panels for context, and icons for quick results.
    """

    def __init__(self):
        """Initializes the UI manager with a rich console and prompt_toolkit components."""
        self.console = Console()
        self.history = InMemoryHistory()
        self.completer = WordCompleter([
            'send', 'look', 'add', 'regenerate', 'save', 'list', 'open', 'run', 'start',
            'backend', 'models', 'personality', 'memory', 'config', 'help', 'exit', 'edit', 'history'
        ], ignore_case=True)
        # Style for highlighted autocompletion to make suggestions more visible
        self.prompt_style = Style.from_dict({
            'prompt': 'bold cyan',
        })

    def get_user_input(self, prompt_text: str) -> str:
        """
        Gets user input with history and autocompletion.

        Args:
            prompt_text: The text to display for the prompt.

        Returns:
            The string entered by the user.
        """
        try:
            # Uses prompt_toolkit for a rich input experience with history and completion
            return prompt(
                prompt_text,
                history=self.history,
                completer=self.completer,
                style=self.prompt_style
            )
        except Exception:
            # Fallback to basic input if prompt_toolkit fails
            self.console.print("[yellow]Warning: Falling back to basic input.[/]")
            return input(prompt_text)

    def display_history(self, history_text: str) -> None:
        """
        Displays the chat history in a formatted panel.

        Args:
            history_text: A string containing the conversation history.
        """
        if not history_text.strip():
            self.console.print("[dim]No history yet.[/]")
            return

        lines = history_text.split("\n")
        colored_text = Text()
        for line in lines:
            if line.startswith("User:"):
                colored_text.append(line + "\n", style="bold blue")
            elif line.startswith("AI:"):
                colored_text.append(line + "\n", style="bold green")
            elif line.startswith("File "):
                colored_text.append(line + "\n", style="yellow")
            else:
                colored_text.append(line + "\n")

        self.console.print(Panel(colored_text, title="[bold magenta]Chat History[/]", border_style="magenta", expand=False, box=box.ROUNDED))

    @contextmanager
    def show_spinner(self, message: str):
        """
        Displays a spinner for long-running operations.

        Args:
            message: The message to display next to the spinner.
        """
        try:
            with self.console.status(f"[bold yellow]{message}[/]", spinner="dots") as status:
                yield status
        except Exception as e:
            self.console.print(f"[dim]UI Warning: Advanced spinner not supported ({e}). Using fallback.[/dim]")
            self.console.print(f"{message}")
            yield
        finally:
            # The spinner stops automatically on context exit
            pass

    def display_status_panel(self, personality: str, backend: str, model: str, msg_count: int, look_count: int) -> None:
        """
        Displays a panel with the current status of the application.

        Args:
            personality: The name of the current AI personality.
            backend: The current backend being used (e.g., 'ollama', 'openrouter').
            model: The specific model in use.
            msg_count: The number of messages in the current session's memory.
            look_count: The number of files loaded into memory.
        """
        status_text = (
            f"[bold]Personality:[/] [green]{personality}[/] | "
            f"[bold]Backend:[/] [green]{backend}[/] | "
            f"[bold]Model:[/] [green]{model}[/] | "
            f"[bold]Memory:[/] {msg_count} messages, {look_count} files"
        )
        self.console.print(Panel(status_text, title="[bold cyan]Status[/]", border_style="cyan", expand=False, box=box.MINIMAL))

    def show_success(self, message: str) -> None:
        """
        Displays a success message.

        Args:
            message: The success message to display.
        """
        self.console.print(f"[green]✅ {message}[/]")

    def show_error(self, message: str) -> None:
        """
        Displays an error message.

        Args:
            message: The error message to display.
        """
        self.console.print(f"[red]❌ {message}[/]")