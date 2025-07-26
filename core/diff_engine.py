import astor
import ast
from typing import Union
import difflib
from typing import List
import sys
from typing import Union, List
from utils.color_formatter import ColorFormatter


def generate_diff_text(original_ast: Union[ast.AST, str], modified_ast:
    Union[ast.AST, str], colored: bool=False) ->str:
    """
    Generate unified diff text between original and modified ASTs or source code strings.

    Args:
        original_ast: Original AST object or source code string
        modified_ast: Modified AST object or source code string
        colored: Whether to generate colored output for terminal display

    Returns:
        Unified diff text as a string
    """
    if isinstance(original_ast, ast.AST):
        original_source = astor.to_source(original_ast)
    else:
        original_source = original_ast
    if isinstance(modified_ast, ast.AST):
        modified_source = astor.to_source(modified_ast)
    else:
        modified_source = modified_ast
    diff = difflib.unified_diff(original_source.splitlines(keepends=True),
        modified_source.splitlines(keepends=True), fromfile='original',
        tofile='modified')
    diff_text = ''.join(diff)
    if colored:
        colored_lines = []
        for line in diff_text.splitlines(keepends=True):
            stripped = line.rstrip('\n')
            if stripped.startswith('+') and not stripped.startswith('+++'):
                colored_lines.append('\x1b[32m' + line + '\x1b[0m')
            elif stripped.startswith('-') and not stripped.startswith('---'):
                colored_lines.append('\x1b[31m' + line + '\x1b[0m')
            elif stripped.startswith('@'):
                colored_lines.append('\x1b[36m' + line + '\x1b[0m')
            else:
                colored_lines.append(line)
        return ''.join(colored_lines)
    return diff_text


"""
Diff Engine - Utilities for generating and displaying code diffs.

This module provides functions for generating unified diffs and
displaying them in a colorized format in the terminal.
"""


def generate_unified_diff(original_lines: List[str], modified_lines: List[
    str], fromfile: str='original', tofile: str='modified') ->List[str]:
    """
    Generate a unified diff between two sets of lines.

    Args:
        original_lines: Lines from the original file/content.
        modified_lines: Lines from the modified file/content.
        fromfile: Name to display for the original file.
        tofile: Name to display for the modified file.

    Returns:
        A list of strings representing the unified diff.
    """
    return list(difflib.unified_diff(original_lines, modified_lines,
        fromfile=fromfile, tofile=tofile, lineterm=''))


def show_diff(diff_lines: Union[List[str], str], stream=sys.stdout) ->None:
    """
    Display a colorized diff in the terminal.

    Adds colors to added/deleted lines for better readability.
    Green for additions (+), red for deletions (-), yellow for headers, and white for context.

    Args:
        diff_lines: A list of diff lines or a single diff string.
        stream: Output stream (default: sys.stdout).
    """
    if isinstance(diff_lines, str):
        lines = diff_lines.splitlines(keepends=True)
    else:
        lines = diff_lines
    formatter = ColorFormatter()
    for line in lines:
        stripped = line.rstrip('\n')
        if stripped.startswith('+') and not stripped.startswith('+++'):
            stream.write(formatter.format_line(line, 'green'))
        elif stripped.startswith('-') and not stripped.startswith('---'):
            stream.write(formatter.format_line(line, 'red'))
        elif stripped.startswith('@'):
            stream.write(formatter.format_line(line, 'cyan'))
        elif stripped.startswith('+++') or stripped.startswith('---'):
            stream.write(formatter.format_line(line, 'yellow'))
        else:
            stream.write(line)
