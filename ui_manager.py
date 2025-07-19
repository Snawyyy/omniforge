from typing import List
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.status import Status
from rich import box
from contextlib import contextmanager
from rich.markup import escape
try:
    from prompt_toolkit import prompt
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.history import InMemoryHistory
    from prompt_toolkit.styles import Style
except ImportError:
    print(
        '[yellow]prompt_toolkit not installed. Falling back to basic input.[/]'
        )
    prompt = input


class UIManager:
    """Manages interactive text-based UI with rich for display and prompt_toolkit for input."""

    def __init__(self):
        """Initializes the UI manager with a rich console and prompt_toolkit components."""
        self.console = Console()
        self.history = InMemoryHistory()
        self.completer = WordCompleter(['send', 'look', 'look_all',
            'create', 'edit', 'refactor', 'commit', 'save', 'list', 'run',
            'history', 'memory', 'backend', 'models', 'set', 'personality',
            'help', 'exit'], ignore_case=True)
        self.prompt_style = Style.from_dict({'prompt': 'bold cyan'})

    def get_user_input(self, prompt_text: str) ->str:
        try:
            return prompt(prompt_text, history=self.history, completer=self
                .completer, style=self.prompt_style)
        except Exception:
            self.console.print(
                '[yellow]Warning: Falling back to basic input.[/]')
            return input(prompt_text)

    def display_history(self, history_text: str) ->None:
        if not history_text.strip():
            self.console.print('[dim]No history yet.[/]')
            return
        lines = history_text.split('\n')
        colored_text = Text()
        for line in lines:
            if line.startswith('User:'):
                colored_text.append(line + '\n', style='bold blue')
            elif line.startswith('AI:'):
                colored_text.append(line + '\n', style='bold green')
            elif line.startswith('File '):
                colored_text.append(line + '\n', style='yellow')
            else:
                colored_text.append(line + '\n')
        self.console.print(Panel(colored_text, title=
            '[bold magenta]Chat History[/]', border_style='magenta', expand
            =False, box=box.ROUNDED))

    @contextmanager
    def show_spinner(self, message: str):
        self.console.print(f'[bold yellow]{message}[/]')
        yield

    def display_status_panel(self, personality: str, backend: str, model:
        str, msg_count: int, look_count: int) ->None:
        status_text = (
            f'[bold]Personality:[/] [green]{personality}[/] | [bold]Backend:[/] [green]{backend}[/] | [bold]Model:[/] [green]{model}[/] | [bold]Memory:[/] {msg_count} messages, {look_count} files'
            )
        self.console.print(Panel(status_text, title='[bold cyan]Status[/]',
            border_style='cyan', expand=False, box=box.MINIMAL))

    def show_success(self, message: str) ->None:
        self.console.print(f'[green]✅ {message}[/]')

    def show_error(self, message: str) ->None:
        """
        Displays an error message, escaping any markup in the message.
        """
        safe_message = escape(str(message))
        self.console.print(f'[red]❌ {safe_message}[/]')
