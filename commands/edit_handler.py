from code_editor import CodeEditor
from utils.logger import log_edit_event
from utils.io_helpers import confirm_change
from core.diff_engine import show_diff
from core.model_client import send_prompt_to_model
from core.prompt_builder import build_edit_prompt
import os


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
    context = {'file_path': file_path, 'element_name': element_name,
        'original_source': original_source, 'instruction': instruction}
    prompt = build_edit_prompt(context)
    if not prompt:
        print('[ERROR] Failed to construct prompt for model.')
        return False
    model_response = send_prompt_to_model(prompt, model)
    if not model_response:
        print('[ERROR] No response received from model.')
        return False
    success = editor.replace_element(element_name, model_response)
    if not success:
        print('[ERROR] Failed to apply changes to the AST.')
        return False
    diff_lines = editor.get_diff()
    if not diff_lines:
        print('[INFO] No changes detected.')
        return False
    show_diff(diff_lines)
    if not confirm_change(diff_lines):
        print('[INFO] Edit canceled by user.')
        return False
    try:
        editor.save_changes()
        log_edit_event(file_path, element_name, instruction, model)
        print(f"[SUCCESS] Edit applied to '{element_name}' in {file_path}")
        return True
    except Exception as e:
        print(f'[ERROR] Failed to save changes: {e}')
        return False
