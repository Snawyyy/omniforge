from typing import List, Union
import sys
import difflib
from typing import Union, List


def format_colored_diff(diff_lines: Union[List[str], str], stream=None) ->str:
    """
    Format and colorize diff output for better readability in terminal.
    
    Args:
        diff_lines: A list of diff lines or a single diff string
        stream: Output stream (default: None returns formatted string)
        
    Returns:
        Formatted diff string if stream is None, otherwise None
    """
    if stream is None:
        stream = sys.stdout
    if isinstance(diff_lines, str):
        lines = diff_lines.splitlines(keepends=True)
    else:
        lines = diff_lines
    output = []
    for line in lines:
        stripped = line.rstrip('\n')
        if stripped.startswith('+') and not stripped.startswith('+++'):
            colored_line = '\x1b[32m' + line + '\x1b[0m'
        elif stripped.startswith('-') and not stripped.startswith('---'):
            colored_line = '\x1b[31m' + line + '\x1b[0m'
        elif stripped.startswith('@'):
            colored_line = '\x1b[36m' + line + '\x1b[0m'
        else:
            colored_line = line
        if stream:
            stream.write(colored_line)
        else:
            output.append(colored_line)
    if not stream:
        return ''.join(output)
