from utils.logger import log_execution_step
from utils.io_helpers import safe_write_file
from core.diff_engine import generate_diff_text
from core.ast_utils import apply_model_patch
from typing import List, Dict, Any
import shutil
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import difflib
from typing import List, Dict, Any, Tuple


def execute_all_step(validated_plan: List[Dict[str, Any]]) ->Tuple[bool,
    List[Dict[str, Any]]]:
    """
    Execute a list of validated transformation steps across multiple files.

    Args:
        validated_plan: A list of step dictionaries containing file paths and operations.

    Returns:
        A tuple containing:
        - Boolean indicating if all steps were successful
        - List of step results with status and error information
    """
    step_results = []
    all_succeeded = True
    for i, step in enumerate(validated_plan):
        action = step.get('action')
        file_path = step.get('file_path')
        step_result = {'index': i, 'action': action, 'file_path': file_path,
            'success': True, 'error': None}
        try:
            if action == 'CREATE':
                content = step.get('content', '')
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w') as f:
                    f.write(content)
                log_execution_step(f'Created file {file_path}')
            elif action == 'MODIFY':
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f'File {file_path} does not exist')
                with open(file_path, 'r') as f:
                    original_content = f.read()
                modified_content = step.get('content', original_content)
                safe_write_file(file_path, modified_content)
                log_execution_step(f'Modified file {file_path}')
            elif action == 'DELETE':
                if os.path.exists(file_path):
                    os.remove(file_path)
                    log_execution_step(f'Deleted file {file_path}')
                else:
                    log_execution_step(
                        f'File {file_path} not found for deletion')
            elif action == 'RENAME':
                new_path = step.get('new_path')
                if os.path.exists(file_path) and new_path:
                    shutil.move(file_path, new_path)
                    log_execution_step(f'Renamed {file_path} to {new_path}')
                else:
                    raise FileNotFoundError(
                        f'Could not rename {file_path} to {new_path}')
            else:
                raise ValueError(f'Unknown action type: {action}')
        except Exception as e:
            all_succeeded = False
            step_result['success'] = False
            step_result['error'] = str(e)
            log_execution_step(
                f'Error executing step {i} ({action} on {file_path}): {str(e)}'
                )
        step_results.append(step_result)
    return all_succeeded, step_results


"""
Executor - Core execution engine for planned transformations

This module provides the core functionality to execute planned code
transformations, including simulation and preview capabilities.
"""
try:
    import astor
    ASTOR_AVAILABLE = True
except ImportError:
    ASTOR_AVAILABLE = False
    print('Warning: astor not installed. Some features may be limited.')


class ExecutionError(Exception):
    """Custom exception for execution-related errors."""
    pass


def simulate_proposed_changes(validated_plan: List[Dict[str, Any]]) ->str:
    """
    Simulate and preview proposed changes before execution.
    
    This function takes a validated transformation plan and generates
    a unified diff showing what changes would be made if the plan
    were executed. It supports CREATE, MODIFY, and DELETE operations.
    
    Args:
        validated_plan: A list of validated transformation steps.
        
    Returns:
        A string containing the unified diff of all proposed changes.
        
    Raises:
        ExecutionError: If there's an error processing any step.
    """
    if not validated_plan:
        return ''
    all_diffs = []
    for step in validated_plan:
        operation = step.get('operation', '').upper()
        try:
            if operation == 'CREATE':
                diff = _simulate_create_step(step)
            elif operation == 'MODIFY':
                diff = _simulate_modify_step(step)
            elif operation == 'DELETE':
                diff = _simulate_delete_step(step)
            else:
                raise ExecutionError(f'Unknown operation: {operation}')
            if diff:
                all_diffs.append(diff)
        except Exception as e:
            raise ExecutionError(
                f"Error simulating step {step.get('path', 'unknown')}: {e}")
    return '\n'.join(all_diffs)


def _simulate_create_step(step: Dict[str, Any]) ->str:
    """Simulate a file creation step."""
    path = step.get('path')
    content = step.get('content', '')
    if not path:
        raise ExecutionError('CREATE step missing path')
    return ''.join(difflib.unified_diff([], content.splitlines(keepends=
        True), fromfile='/dev/null', tofile=f'a/{path}'))


def _simulate_modify_step(step: Dict[str, Any]) ->str:
    """Simulate a file modification step."""
    path = step.get('path')
    content = step.get('content', '')
    if not path:
        raise ExecutionError('MODIFY step missing path')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            original_content = f.read()
    except FileNotFoundError:
        return ''.join(difflib.unified_diff([], content.splitlines(keepends
            =True), fromfile='/dev/null', tofile=f'a/{path}'))
    except Exception as e:
        raise ExecutionError(f'Error reading file {path}: {e}')
    return ''.join(difflib.unified_diff(original_content.splitlines(
        keepends=True), content.splitlines(keepends=True), fromfile=
        f'a/{path}', tofile=f'b/{path}'))


def _simulate_delete_step(step: Dict[str, Any]) ->str:
    """Simulate a file deletion step."""
    path = step.get('path')
    if not path:
        raise ExecutionError('DELETE step missing path')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            original_content = f.read()
    except FileNotFoundError:
        return f'\\ No such file: {path}\n'
    except Exception as e:
        raise ExecutionError(f'Error reading file {path}: {e}')
    return ''.join(difflib.unified_diff(original_content.splitlines(
        keepends=True), [], fromfile=f'a/{path}', tofile='/dev/null'))
