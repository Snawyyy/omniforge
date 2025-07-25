import astor
from ast import AST
from typing import Union
import shutil
import os
from typing import TextIO
import sys
from utils.logger import log_debug


def safe_write_file(file_path: str, content: Union[str, AST], create_backup:
    bool=True) ->bool:
    """
    Safely writes content to a file, optionally creating a backup of the original.

    Args:
        file_path: The path to the file to write.
        content: The content to write (either a string or an AST node).
        create_backup: Whether to create a backup of the original file.

    Returns:
        True if the write was successful, False otherwise.
    """
    if create_backup and os.path.exists(file_path):
        try:
            backup_path = f'{file_path}.backup'
            shutil.copy2(file_path, backup_path)
        except Exception as e:
            print(f'[WARNING] Failed to create backup: {e}')
    if isinstance(content, AST):
        try:
            content = astor.to_source(content)
        except Exception as e:
            print(f'[ERROR] Failed to convert AST to source: {e}')
            return False
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f'[ERROR] Failed to write to file: {e}')
        if create_backup and os.path.exists(f'{file_path}.backup'):
            try:
                shutil.move(f'{file_path}.backup', file_path)
                print('[INFO] Restored from backup.')
            except Exception as restore_error:
                print(f'[ERROR] Failed to restore from backup: {restore_error}'
                    )
        return False


def confirm_change(diff_text: str, input_stream: TextIO=sys.stdin) ->bool:
    """
    Prompt the user to confirm or reject changes based on a diff.

    Args:
        diff_text: The diff string showing proposed changes.
        input_stream: Input stream to read from (default: stdin).

    Returns:
        True if user confirms, False otherwise.
    """
    if not diff_text.strip():
        return True
    print('\nProposed changes:')
    print(diff_text)
    while True:
        response = input_stream.readline().strip().lower()
        if response in ('y', 'yes'):
            return True
        elif response in ('n', 'no'):
            return False
        else:
            print("Please respond with 'y' (yes) or 'n' (no): ", end='')


def confirm_plan_execution(diff_preview: str) ->bool:
    """
    Prompt the user to confirm plan execution after showing a diff preview.

    Args:
        diff_preview (str): The formatted diff output to display for review.

    Returns:
        bool: True if user confirms, False otherwise.
    """
    log_debug('Displaying refactor plan diff for confirmation.')
    print(diff_preview)
    print('\nProceed with applying these changes? (y/n): ', end='')
    try:
        choice = input().strip().lower()
        if choice in ('y', 'yes'):
            return True
        else:
            return False
    except KeyboardInterrupt:
        print('\nOperation canceled by user.')
        sys.exit(0)
    except Exception as e:
        log_debug(f'Error reading user input: {e}')
        return False
