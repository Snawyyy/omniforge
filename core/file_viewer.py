from pathlib import Path
from typing import List, Dict, Any, Optional
import re
import fnmatch
import os
from core.ast_utils import get_file_language
from utils.logger import log_function_call
from typing import List, Dict, Any


def view_files_by_pattern(pattern: str, project_root: str) ->List[Dict[str,
    Any]]:
    """
    View files matching a given pattern with metadata.
    
    Args:
        pattern: File pattern to match (e.g., '*.py', 'config/*')
        project_root: Root directory of the project
        
    Returns:
        List of dictionaries containing file metadata
    """
    log_function_call('view_files_by_pattern', pattern)
    matched_files = []
    for root, _, files in os.walk(project_root):
        for filename in files:
            filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(filepath, project_root)
            if fnmatch.fnmatch(rel_path, pattern):
                file_info = {'path': rel_path, 'language':
                    get_file_language(filepath), 'size': os.path.getsize(
                    filepath)}
                if file_info['language'] != 'unknown':
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            file_info['snippet'] = ''.join(lines[:10])
                    except UnicodeDecodeError:
                        file_info['snippet'] = '<Binary file>'
                else:
                    file_info['snippet'] = '<Non-code file>'
                matched_files.append(file_info)
    return matched_files
