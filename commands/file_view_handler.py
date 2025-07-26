from core.executor import execute_file_operation
from core.planner import get_project_file_list
from utils.logger import log_command_execution
from utils.io_helpers import display_file_content
from typing import List
from core.model_client import ModelClient
from utils.io_helpers import read_file_safe
from utils.logger import log_command
from typing import Dict, Any, List, Optional
import json
import os
"""
File View Handler - A command handler for viewing file contents.

This module provides functionality to view the contents of specified files
from the project manifest, supporting both single file viewing and batch operations.
"""


def handle_file_view_command(command_data: Dict[str, Any]) ->Dict[str, Any]:
    """
    Handle the file view command to display content of specified files.
    
    Args:
        command_data: Dictionary containing command parameters including:
            - files: List of file paths to view
            - project_root: Root directory of the project
            - context_lines: Number of context lines to show around matches (optional)
            
    Returns:
        Dictionary with results of the file view operation.
    """
    try:
        files_to_view = command_data.get('files', [])
        project_root = command_data.get('project_root', '.')
        context_lines = command_data.get('context_lines', 0)
        if not files_to_view:
            return {'success': False, 'error':
                'No files specified for viewing', 'files_viewed': []}
        viewed_files = []
        errors = []
        for file_path in files_to_view:
            try:
                full_path = os.path.join(project_root, file_path)
                if not os.path.exists(full_path):
                    errors.append(f'File not found: {file_path}')
                    continue
                content = read_file_safe(full_path)
                if content is None:
                    errors.append(f'Could not read file: {file_path}')
                    continue
                viewed_files.append({'path': file_path, 'content': content,
                    'size': len(content)})
            except Exception as e:
                errors.append(f'Error viewing {file_path}: {str(e)}')
        result = {'success': True, 'files_viewed': viewed_files, 'errors':
            errors}
        log_command('file_view', result)
        return result
    except Exception as e:
        return {'success': False, 'error':
            f'Command execution failed: {str(e)}', 'files_viewed': []}
