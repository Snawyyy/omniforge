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


def handle_edit_command(file_path: str, element_name: str, instruction: str,
    model: str='default') ->bool:
    """
    Main handler for the `edit` command - orchestrates the full edit workflow.

    Args:
        file_path: Path to the target Python file.
        element_name: Name of the function/class to edit.
        instruction: User-provided instruction for the edit.
        model: Name of the model to use for code generation.

    Returns:
        True if edit was successfully applied, False otherwise.
    """
    if not os.path.exists(file_path):
        print(f'[ERROR] File not found: {file_path}')
        return False
    try:
        editor = CodeEditor(file_path)
    except Exception as e:
        print(f'[ERROR] Failed to initialize editor for {file_path}: {e}')
        return False
    if element_name not in editor.list_elements():
        print(f"[ERROR] Element '{element_name}' not found in {file_path}")
        return False
    original_source = editor.get_source_of(element_name)
    if not original_source:
        print(f"[ERROR] Could not retrieve source for '{element_name}'")
        return False
    referenced_files = _extract_referenced_files(instruction)
    additional_context = {}
    for ref_file in referenced_files:
        if os.path.exists(ref_file):
            try:
                with open(ref_file, 'r') as f:
                    additional_context[ref_file] = f.read()
            except Exception as e:
                print(f'[DEBUG] Could not read referenced file {ref_file}: {e}'
                    )
    context = {'file_path': file_path, 'element_name': element_name,
        'original_source': original_source, 'instruction': instruction,
        'additional_context': additional_context}
    try:
        prompt = build_edit_prompt(context)
    except Exception as e:
        print(f'[ERROR] Failed to construct prompt for model: {e}')
        return False
    if not prompt:
        print('[ERROR] Failed to construct prompt for model.')
        return False
    try:
        model_response = send_prompt_to_model(prompt, model)
    except Exception as e:
        print(f'[ERROR] Failed to get response from model: {e}')
        return False
    if not model_response:
        print('[ERROR] No response received from model.')
        return False
    try:
        success = editor.replace_element(element_name, model_response)
    except Exception as e:
        print(f'[ERROR] Failed to apply changes to the AST: {e}')
        return False
    if not success:
        print('[ERROR] Failed to apply changes to the AST.')
        return False
    try:
        diff_lines = editor.get_diff()
    except Exception as e:
        print(f'[ERROR] Failed to generate diff: {e}')
        return False
    if not diff_lines:
        print('[INFO] No changes detected.')
        return False
    try:
        show_diff(diff_lines)
    except Exception as e:
        print(f'[ERROR] Failed to display diff: {e}')
    try:
        if not confirm_change(diff_lines):
            print('[INFO] Edit canceled by user.')
            return False
    except Exception as e:
        print(f'[ERROR] Failed to confirm changes: {e}')
        return False
    try:
        editor.save_changes()
        log_edit_event(file_path, element_name, instruction, model)
        print(f"[SUCCESS] Edit applied to '{element_name}' in {file_path}")
        return True
    except Exception as e:
        print(f'[ERROR] Failed to save changes: {e}')
        return False


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
