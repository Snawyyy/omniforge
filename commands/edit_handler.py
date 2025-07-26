from code_editor import CodeEditor
from utils.logger import log_edit_event
from utils.io_helpers import confirm_change
from core.diff_engine import show_diff
from core.model_client import send_prompt_to_model
from core.prompt_builder import build_edit_prompt
import os
from typing import Optional
from core.diff_engine import generate_diff_text, show_diff
from utils.io_helpers import confirm_change, safe_write_file
import re
from typing import List, Dict


def _extract_referenced_files(instruction: str) ->List[str]:
    """Extract file paths referenced in the instruction."""
    patterns = ['"([^"]*\\.[^"]+)"', "'([^']*\\.[^']+)'",
        '(\x08[\\w./\\-]+\\.[\\w]+\x08)']
    files = []
    for pattern in patterns:
        matches = re.findall(pattern, instruction)
        if matches:
            if isinstance(matches[0], str):
                files.extend(matches)
            else:
                files.extend([m[0] for m in matches])
    valid_files = []
    for f in files:
        if '.' in f and not f.startswith(('http', 'www')):
            valid_files.append(f)
    return list(set(valid_files))


def _extract_referenced_files(instruction: str) ->list:
    """Extract file paths referenced in the instruction."""
    patterns = ['"([^"]*\\.[a-zA-Z]+)"', "'([^']*\\\\.[a-zA-Z]+)'",
        '(\\b[\\w./\\-]+\\.[a-zA-Z]+\\b)']
    files = []
    for pattern in patterns:
        matches = re.findall(pattern, instruction)
        files.extend(matches if isinstance(matches[0], str) else [m[0] for
            m in matches])
    valid_files = []
    for f in files:
        if '.' in f and not f.startswith(('http', 'www')):
            valid_files.append(f)
    return list(set(valid_files))
