from utils.io_helpers import get_file_hash
from utils.logger import log_dynamic_context_event
from memory_manager import get_memory_manager
from pathlib import Path
from typing import List, Optional
import os
import fnmatch
from typing import Dict, List
from typing import List, Set
import re
from typing import List, Dict, Set
from datetime import datetime
"""
Dynamic Context - Runtime file inspection for AI-assisted operations

This module provides functions to dynamically load and inspect files
during refactoring or editing operations, allowing the AI to gather
additional context as needed.
"""


def dynamic_look_at_file(file_path: str, silent: bool=False) ->bool:
    """
    Dynamically inspect a file during execution to load it into context.
    
    Args:
        file_path: Path to the file to inspect
        silent: Whether to suppress output messages
        
    Returns:
        True if file was successfully loaded, False otherwise
    """
    try:
        resolved_path = Path(file_path).resolve()
        if not resolved_path.exists():
            if not silent:
                print(
                    f'[DEBUG] File not found for dynamic inspection: {file_path}'
                    )
            return False
        if not resolved_path.is_file():
            if not silent:
                print(f'[DEBUG] Path is not a file: {file_path}')
            return False
        memory_manager = get_memory_manager()
        if str(resolved_path) in memory_manager.list_loaded_files():
            if not silent:
                print(f'[DEBUG] File already in context: {file_path}')
            return True
        try:
            with open(resolved_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(resolved_path, 'r', encoding='utf-8', errors='ignore'
                    ) as f:
                    content = f.read()
            except Exception:
                if not silent:
                    print(f'[DEBUG] Failed to read file: {file_path}')
                return False
        except Exception:
            if not silent:
                print(f'[DEBUG] Failed to read file: {file_path}')
            return False
        file_info = {'path': str(resolved_path), 'content': content, 'hash':
            get_file_hash(str(resolved_path)), 'size': os.path.getsize(str(
            resolved_path))}
        memory_manager.load_file(str(resolved_path), file_info)
        log_dynamic_context_event(str(resolved_path))
        if not silent:
            print(f'[DEBUG] Dynamically loaded file into context: {file_path}')
        return True
    except Exception as e:
        if not silent:
            print(f'[DEBUG] Failed to dynamically look at {file_path}: {e}')
        return False


def should_dynamically_inspect_file(file_path: str, context_files: List[str]
    ) ->bool:
    """
    Determine if a file should be dynamically inspected based on context.
    
    Args:
        file_path: Path to the file to check
        context_files: List of files already in context
        
    Returns:
        True if file should be inspected, False otherwise
    """
    resolved_path = Path(file_path).resolve()
    if str(resolved_path) in context_files:
        return False
    if resolved_path.suffix.lower() in ['.py', '.js', '.txt', '.json', '.md']:
        return True
    return False


def get_referenced_files_from_content(content: str) ->List[str]:
    """
    Extract potentially referenced file paths from content.
    
    Args:
        content: Text content to analyze
        
    Returns:
        List of referenced file paths
    """
    import re
    referenced_files = []
    patterns = ['["\\\']([^\\s"\\\']+\\.(py|js|json|txt|md))["\\\']',
        'open\\(["\\\']([^\\s"\\\']+\\.(py|js|json|txt|md))["\\\']']
    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                referenced_files.append(match[0])
            else:
                referenced_files.append(match)
    return referenced_files


def should_dynamically_inspect_file(file_path: str, context: Dict) ->bool:
    """
    Determine if a file should be dynamically inspected based on context and relevance.
    
    Args:
        file_path: Path to the file to evaluate
        context: Current operation context containing instruction and project info
        
    Returns:
        True if file should be inspected, False otherwise
    """
    project_root = context.get('project_root', '')
    ignored_patterns = context.get('ignored_patterns', [])
    abs_file_path = os.path.abspath(file_path)
    if not os.path.exists(abs_file_path):
        return False
    rel_path = os.path.relpath(abs_file_path, project_root
        ) if project_root else abs_file_path
    for pattern in ignored_patterns:
        if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(os.path.
            basename(abs_file_path), pattern):
            return False
    instruction = context.get('instruction', '').lower()
    file_name = os.path.basename(abs_file_path).lower()
    if file_name in instruction:
        return True
    _, ext = os.path.splitext(file_path)
    if ext in ['.py', '.json', '.yml', '.yaml', '.txt', '.md']:
        return True
    return False


def extract_referenced_files(instruction: str, project_root: str='.') ->List[
    str]:
    """
    Extract file references from user instructions.
    
    Args:
        instruction: User-provided instruction text
        project_root: Root directory to resolve relative paths
        
    Returns:
        List of resolved file paths mentioned in the instruction
    """
    referenced_files: Set[str] = set()
    quoted_patterns = [
        '["\\\'`]([a-zA-Z0-9_\\-\\/\\\\.\\[\\]{}]+\\.([a-zA-Z0-9_]+))["\\\'`]',
        '["\\\'`]([a-zA-Z0-9_\\-\\/\\\\.\\[\\]{}]+\\.[a-zA-Z]{1,4})["\\\'`]']
    relative_patterns = [
        '(\\.\\/[a-zA-Z0-9_\\-\\/\\\\.\\[\\]{}]+\\.([a-zA-Z0-9_]+))',
        '(\\.\\.\\/[a-zA-Z0-9_\\-\\/\\\\.\\[\\]{}]+\\.([a-zA-Z0-9_]+))',
        '(\\.\\/[a-zA-Z0-9_\\-\\/\\\\.\\[\\]{}]+\\.[a-zA-Z]{1,4})',
        '(\\.\\.\\/[a-zA-Z0-9_\\-\\/\\\\.\\[\\]{}]+\\.[a-zA-Z]{1,4})']
    bare_patterns = [
        '\\b([a-zA-Z0-9_\\-\\/\\\\.\\[\\]{}]+\\.(py|js|json|yaml|yml|md|txt|css|html|jsx|tsx|ts|jsx|scss|sass|less|vue|svelte))\\b'
        ,
        '\\b([a-zA-Z0-9_\\-\\/\\\\.\\[\\]{}]+\\.(py|js|json|y[a]?ml|md|txt|css|html))\\b'
        ]
    all_patterns = quoted_patterns + relative_patterns + bare_patterns
    for pattern in all_patterns:
        matches = re.findall(pattern, instruction, re.IGNORECASE)
        for match in matches:
            file_path = match[0] if isinstance(match, tuple) else match
            if file_path.startswith(('http', 'www', '#', '//', '/*', '<!--')):
                continue
            if file_path.startswith(('./', '../')):
                resolved_path = os.path.normpath(os.path.join(project_root,
                    file_path))
            else:
                resolved_path = os.path.normpath(os.path.join(project_root,
                    file_path))
            if os.path.exists(resolved_path) and os.path.isfile(resolved_path):
                referenced_files.add(resolved_path)
    filtered_files = set()
    common_extensions = {'.py', '.js', '.json', '.yaml', '.yml', '.md',
        '.txt', '.css', '.html', '.jsx', '.tsx', '.ts', '.scss', '.sass',
        '.less', '.vue', '.svelte'}
    for file_path in referenced_files:
        _, ext = os.path.splitext(file_path)
        if ext.lower() in common_extensions:
            filtered_files.add(file_path)
    return list(filtered_files)


def load_dynamic_context_for_refactor(goal: str, project_root: str='.') ->Dict[
    str, str]:
    """
    Load dynamic context for refactor operations by identifying and loading
    relevant files mentioned in the refactor goal.
    
    Args:
        goal: The refactor goal description that may reference files
        project_root: Root directory to resolve relative paths
        
    Returns:
        Dictionary mapping file paths to their contents for referenced files
    """
    referenced_files = _extract_referenced_files_from_goal(goal, project_root)
    context_files = {}
    memory_manager = get_memory_manager()
    for file_path in referenced_files:
        try:
            resolved_path = Path(file_path).resolve()
            if not resolved_path.exists() or not resolved_path.is_file():
                continue
            if str(resolved_path) in memory_manager.list_loaded_files():
                file_info = memory_manager.get_file_info(str(resolved_path))
                context_files[str(resolved_path)] = file_info.get('content', ''
                    )
                continue
            with open(resolved_path, 'r', encoding='utf-8') as f:
                content = f.read()
            file_info = {'path': str(resolved_path), 'content': content,
                'hash': get_file_hash(str(resolved_path)), 'size': os.path.
                getsize(str(resolved_path))}
            memory_manager.load_file(str(resolved_path), file_info)
            context_files[str(resolved_path)] = content
        except Exception:
            continue
    return context_files


def _extract_referenced_files_from_goal(goal: str, project_root: str) ->List[
    str]:
    """
    Extract file paths referenced in a refactor goal description.
    
    Args:
        goal: The refactor goal description
        project_root: Root directory to resolve relative paths
        
    Returns:
        List of resolved file paths mentioned in the goal
    """
    patterns = ['"([^"]*\\.[^"]*)"', "'([^']*\\\\.[^']*)'",
        '`([^`]*\\.[^`]*)`', '\\b([\\w./\\\\-]+\\.[\\w]+)\\b']
    files: Set[str] = set()
    for pattern in patterns:
        matches = re.findall(pattern, goal)
        for match in matches:
            resolved_path = os.path.normpath(os.path.join(project_root, match))
            if os.path.exists(resolved_path) and os.path.isfile(resolved_path):
                files.add(resolved_path)
    valid_extensions = {'.py', '.js', '.jsx', '.ts', '.tsx', '.java',
        '.cpp', '.h', '.cs', '.go', '.rs', '.php', '.rb', '.swift'}
    filtered_files = []
    for f in files:
        if Path(f).suffix.lower() in valid_extensions:
            filtered_files.append(f)
    return filtered_files


def filter_relevant_context(referenced_files: List[str], context_files:
    List[str], max_context_size: int=100000) ->List[str]:
    """
    Filter out irrelevant files and limit context size for dynamic loading.
    
    Args:
        referenced_files: List of files identified as potentially relevant
        context_files: List of files already in context
        max_context_size: Maximum total characters to include in context
        
    Returns:
        List of files to load, filtered and sized appropriately
    """
    context_file_set = set(context_files)
    filtered_files = []
    current_size = 0
    prioritized_files = sorted(referenced_files, key=lambda f: (f in
        context_file_set, not any(f.endswith(ext) for ext in ['.py', '.js',
        '.ts', '.jsx', '.tsx']), os.path.getsize(f) if os.path.exists(f) else
        float('inf')))
    for file_path in prioritized_files:
        if file_path in context_file_set:
            continue
        resolved_path = Path(file_path).resolve()
        if not resolved_path.exists() or not resolved_path.is_file():
            continue
        try:
            file_size = os.path.getsize(str(resolved_path))
            if file_size > 1000000:
                continue
            _, ext = os.path.splitext(str(resolved_path))
            if ext not in ['.py', '.js', '.ts', '.jsx', '.tsx', '.json',
                '.yml', '.yaml', '.md', '.txt']:
                continue
            if current_size + file_size > max_context_size:
                break
            filtered_files.append(str(resolved_path))
            current_size += file_size
        except (OSError, IOError):
            continue
    log_dynamic_context_event(
        f'Filtered {len(filtered_files)} relevant files from {len(referenced_files)} candidates'
        )
    return filtered_files


def filter_relevant_context(instruction: str, project_files: List[str],
    project_root: str='.', max_files: int=10) ->List[str]:
    """
    Filter and prioritize relevant files for dynamic loading based on instruction context.
    
    Args:
        instruction: User instruction to analyze for file references
        project_files: List of all available project files
        project_root: Project root directory for path resolution
        max_files: Maximum number of files to return
        
    Returns:
        List of prioritized file paths most relevant to the instruction
    """
    lower_instruction = instruction.lower()
    file_scores = {}
    for file_path in project_files:
        score = 0
        file_name = os.path.basename(file_path).lower()
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_name in lower_instruction:
            score += 100
        if file_ext in ['.py', '.js', '.json', '.yml', '.yaml']:
            score += 20
        path_parts = file_path.lower().split(os.sep)
        for part in path_parts:
            if part in lower_instruction:
                score += 10
        if any(pattern in file_path.lower() for pattern in ['config',
            'util', 'helper', 'service', 'model', 'controller']):
            score += 15
        file_scores[file_path] = score
    sorted_files = sorted(file_scores.items(), key=lambda x: x[1], reverse=True
        )
    relevant_files = [file_path for file_path, score in sorted_files if 
        score > 0][:max_files]
    for file_path in relevant_files:
        log_dynamic_context_event(
            f'Prioritized context file: {file_path} (score: {file_scores[file_path]})'
            )
    return relevant_files
