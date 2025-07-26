from typing import List, Optional, Callable
import os
import fnmatch
"""
File Filters - Utility functions for filtering files based on patterns.

This module provides functions to filter files by various patterns,
supporting both inclusion and exclusion criteria.
"""


def filter_files_by_pattern(file_paths: List[str], include_patterns:
    Optional[List[str]]=None, exclude_patterns: Optional[List[str]]=None,
    base_path: Optional[str]=None) ->List[str]:
    """
    Filter a list of file paths based on include and exclude patterns.

    This function applies glob-style pattern matching to filter files.
    Include patterns act as a whitelist, while exclude patterns act as a blacklist.
    If include_patterns is provided, only files matching those patterns are considered.
    Then, exclude_patterns are applied to remove files from the result.

    Args:
        file_paths: List of file paths to filter.
        include_patterns: Optional list of glob patterns for inclusion.
                         If provided, only files matching these patterns are included.
        exclude_patterns: Optional list of glob patterns for exclusion.
                         Files matching these patterns are excluded from results.
        base_path: Optional base path to resolve relative patterns against.

    Returns:
        A list of file paths that match the filtering criteria.

    Examples:
        >>> files = ['src/main.py', 'tests/test_main.py', 'README.md']
        >>> filter_files_by_pattern(files, include_patterns=['*.py'])
        ['src/main.py', 'tests/test_main.py']
        
        >>> filter_files_by_pattern(files, exclude_patterns=['tests/*'])
        ['src/main.py', 'README.md']
        
        >>> filter_files_by_pattern(files, include_patterns=['*.py'], exclude_patterns=['tests/*'])
        ['src/main.py']
    """
    result = file_paths.copy()
    if include_patterns:
        included_files = set()
        for pattern in include_patterns:
            if base_path and not os.path.isabs(pattern):
                pattern = os.path.join(base_path, pattern)
            for file_path in result:
                full_path = file_path
                if base_path and not os.path.isabs(file_path):
                    full_path = os.path.join(base_path, file_path)
                if fnmatch.fnmatch(full_path, pattern) or fnmatch.fnmatch(os
                    .path.basename(file_path), pattern):
                    included_files.add(file_path)
        result = list(included_files)
    if exclude_patterns:
        for pattern in exclude_patterns:
            if base_path and not os.path.isabs(pattern):
                pattern = os.path.join(base_path, pattern)
            result = [file_path for file_path in result if not (fnmatch.
                fnmatch(file_path, pattern) or base_path and fnmatch.
                fnmatch(os.path.join(base_path, file_path), pattern) or
                fnmatch.fnmatch(os.path.basename(file_path), pattern))]
    return result


def create_file_filter(include_patterns: Optional[List[str]]=None,
    exclude_patterns: Optional[List[str]]=None, base_path: Optional[str]=None
    ) ->Callable[[List[str]], List[str]]:
    """
    Create a reusable file filter function with predefined patterns.

    This factory function returns a filter function that can be applied to
    multiple lists of file paths with the same patterns.

    Args:
        include_patterns: Optional list of glob patterns for inclusion.
        exclude_patterns: Optional list of glob patterns for exclusion.
        base_path: Optional base path to resolve relative patterns against.

    Returns:
        A function that takes a list of file paths and returns filtered results.
        
    Example:
        >>> is_python_file = create_file_filter(include_patterns=['*.py'])
        >>> files = ['main.py', 'README.md', 'utils.py']
        >>> is_python_file(files)
        ['main.py', 'utils.py']
    """

    def filter_function(file_paths: List[str]) ->List[str]:
        return filter_files_by_pattern(file_paths, include_patterns=
            include_patterns, exclude_patterns=exclude_patterns, base_path=
            base_path)
    return filter_function
