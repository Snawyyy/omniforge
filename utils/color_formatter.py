import sys
from typing import Optional


class ColorFormatter:
    """Handles colored output formatting for terminal display."""
    GREEN = '\x1b[92m'
    RED = '\x1b[91m'
    YELLOW = '\x1b[93m'
    BLUE = '\x1b[94m'
    BOLD = '\x1b[1m'
    UNDERLINE = '\x1b[4m'
    RESET = '\x1b[0m'

    @classmethod
    def green(cls, text: str) ->str:
        """Format text with green color."""
        return f'{cls.GREEN}{text}{cls.RESET}'

    @classmethod
    def red(cls, text: str) ->str:
        """Format text with red color."""
        return f'{cls.RED}{text}{cls.RESET}'

    @classmethod
    def yellow(cls, text: str) ->str:
        """Format text with yellow color."""
        return f'{cls.YELLOW}{text}{cls.RESET}'

    @classmethod
    def blue(cls, text: str) ->str:
        """Format text with blue color."""
        return f'{cls.BLUE}{text}{cls.RESET}'

    @classmethod
    def bold(cls, text: str) ->str:
        """Format text with bold styling."""
        return f'{cls.BOLD}{text}{cls.RESET}'

    @classmethod
    def underline(cls, text: str) ->str:
        """Format text with underline styling."""
        return f'{cls.UNDERLINE}{text}{cls.RESET}'

    @classmethod
    def success(cls, text: str) ->str:
        """Format success message with green color."""
        return cls.green(text)

    @classmethod
    def error(cls, text: str) ->str:
        """Format error message with red color."""
        return cls.red(text)

    @classmethod
    def warning(cls, text: str) ->str:
        """Format warning message with yellow color."""
        return cls.yellow(text)

    @classmethod
    def info(cls, text: str) ->str:
        """Format info message with blue color."""
        return cls.blue(text)

    @classmethod
    def supports_color(cls) ->bool:
        """Check if the terminal supports color output."""
        return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()

    @classmethod
    def format_if_supported(cls, text: str, formatter) ->str:
        """Apply formatting only if terminal supports it."""
        if cls.supports_color():
            return formatter(text)
        return text
