from typing import List
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.status import Status
from rich import box
from contextlib import contextmanager
from rich.markup import escape
import gc

try:
    from prompt_toolkit import prompt
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.history import InMemoryHistory
    from prompt_toolkit.styles import Style
except ImportError:
    print('[yellow]prompt_toolkit not installed. Falling back to basic input.[/]')
    prompt = input


class UIManager:
    """Manages interactive text-based UI with rich for display and prompt_toolkit for input."""
    
    def __init__(self):
        """Initializes the UI manager with a rich console and prompt_toolkit components."""
        self.console = Console()
        self.history = InMemoryHistory()
        self.completer = WordCompleter([
            'send', 'look', 'look_all', 'create', 'edit', 'refactor', 'commit',
            'save', 'list', 'run', 'history', 'memory', 'backend', 'models',
            'set', 'personality', 'help', 'exit'
        ], ignore_case=True)
        self.prompt_style = Style.from_dict({'prompt': 'bold cyan'})

    def get_user_input(self, prompt_text: str) -> str:
        try:
            return prompt(prompt_text, history=self.history, completer=self.completer, style=self.prompt_style)
        except Exception:
            self.console.print('[yellow]Warning: Falling back to basic input.[/]')
            return input(prompt_text)

    def display_history(self, history_text: str) -> None:
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
        
        self.console.print(Panel(
            colored_text, 
            title='[bold magenta]Chat History[/]', 
            border_style='magenta', 
            expand=False, 
            box=box.ROUNDED
        ))

    @contextmanager
    def show_spinner(self, message: str):
        """
        Context manager that displays a spinner with the given message.
        Handles Rich LiveError by cleaning up stuck live displays and 
        ensuring proper cleanup on exceptions.
        
        Usage:
            with ui_manager.show_spinner("Loading..."):
                # do work here
        """
        # Initialize spinner state if not exists
        if not hasattr(self, '_spinner_active'):
            self._spinner_active = False
        
        # If spinner is already active, just yield without additional output
        if self._spinner_active:
            try:
                yield
            except Exception as e:
                raise e
            return
        
        # Clean up any stuck Rich live displays before starting
        self._cleanup_stuck_rich_displays()
        
        # Mark spinner as active
        self._spinner_active = True
        status_context = None
        
        try:
            # Try to use rich status, but with fallback
            try:
                status_context = self.console.status(f'[bold yellow]{message}[/]')
                status_context.__enter__()
            except Exception:
                # If rich.status fails, fallback to static print
                status_context = None
                self.console.print(f'[bold yellow]{message}[/]')
            
            yield
            
        except Exception as e:
            # Re-raise actual work errors
            raise e
            
        finally:
            # Always cleanup spinner state and rich display
            self._spinner_active = False
            if status_context is not None:
                try:
                    status_context.__exit__(None, None, None)
                except:
                    pass  # Suppress cleanup errors
            
            # Force cleanup any remaining rich displays
            self._cleanup_stuck_rich_displays()

    def _cleanup_stuck_rich_displays(self):
        """
        Clean up stuck Rich live displays that prevent new ones from starting.
        Based on solution from: https://github.com/DLR-RM/stable-baselines3/issues/1645
        """
        try:
            # Method 1: Reset console live display if exists
            if hasattr(self.console, '_live') and self.console._live is not None:
                try:
                    self.console._live.stop()
                    self.console._live = None
                except:
                    pass
            
            # Method 2: Find and close stuck rich/tqdm objects using garbage collection
            rich_objects = [obj for obj in gc.get_objects() 
                        if hasattr(obj, '__class__') and 
                        ('live' in type(obj).__name__.lower() or 
                            'progress' in type(obj).__name__.lower() or
                            'status' in type(obj).__name__.lower()) and
                        hasattr(obj, 'stop')]
            
            for rich_obj in rich_objects:
                try:
                    if hasattr(rich_obj, 'stop'):
                        rich_obj.stop()
                    elif hasattr(rich_obj, 'close'):
                        rich_obj.close()
                except:
                    pass  # Suppress cleanup errors
                    
        except:
            pass  # Suppress all cleanup errors to avoid breaking the main flow

    def display_status_panel(self, personality: str, backend: str, model: str, msg_count: int, look_count: int) -> None:
        status_text = (
            f'[bold]Personality:[/] [green]{personality}[/] | '
            f'[bold]Backend:[/] [green]{backend}[/] | '
            f'[bold]Model:[/] [green]{model}[/] | '
            f'[bold]Memory:[/] {msg_count} messages, {look_count} files'
        )
        self.console.print(Panel(
            status_text, 
            title='[bold cyan]Status[/]', 
            border_style='cyan', 
            expand=False, 
            box=box.MINIMAL
        ))

    def show_success(self, message: str) -> None:
        self.console.print(f'[green]✅ {message}[/]')

    def show_error(self, message: str) -> None:
        """
        Displays an error message, escaping any markup in the message.
        """
        safe_message = escape(str(message))
        self.console.print(f'[red]❌ {safe_message}[/]')