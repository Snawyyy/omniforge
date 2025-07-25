from ast_adapter import ASTAdapter
from typing import List, Optional, Dict, Any
"""
TextAdapter - Concrete AST adapter for plain text files.

This module implements the ASTAdapter interface specifically for plain text files,
treating the entire file content as a single element.
"""


class TextAdapter(ASTAdapter):
    """
    Concrete implementation of ASTAdapter for plain text files.

    This adapter treats the entire text file content as a single element
    that can be manipulated using the ASTAdapter interface.
    """

    def __init__(self, source_code: str):
        """
        Initializes the TextAdapter with the source code.

        Args:
            source_code: The text content as a string.
        """
        self.source_code: str = source_code
        super().__init__(source_code)

    def _parse_and_map(self, source_code: str) ->None:
        """
        Creates a simple mapping for the text content.

        Args:
            source_code: The text content string.
        """
        self.nodes = {'content': source_code}

    def list_elements(self) ->List[str]:
        """Lists the names of the main elements (just 'content' for text files)."""
        return ['content']

    def get_source_of(self, element_name: str) ->Optional[str]:
        """Gets the source code string for a specific named element."""
        if element_name == 'content':
            return self.source_code
        return None

    def get_element_structure(self, element_name: str) ->Optional[Dict]:
        """Gets detailed structural information about an element."""
        if element_name == 'content':
            return {'name': element_name, 'type': 'TextContent',
                'line_start': 1, 'line_end': len(self.source_code.
                splitlines()), 'body_items': []}
        return None

    def get_element_body_snippet(self, element_name: str, line_start: int,
        line_end: int) ->Optional[str]:
        """Extracts a snippet of code from within an element's body."""
        if element_name != 'content':
            return None
        lines = self.source_code.splitlines()
        if 1 <= line_start <= len(lines) and 1 <= line_end <= len(lines
            ) and line_start <= line_end:
            return '\n'.join(lines[line_start - 1:line_end])
        return None

    def replace_element(self, element_name: str, new_code: str) ->bool:
        """Replaces a named element with new code."""
        if element_name == 'content':
            self.source_code = new_code
            self._parse_and_map(new_code)
            return True
        return False

    def add_element(self, new_code: str, anchor_name: Optional[str]=None,
        before: bool=False) ->bool:
        """Adds a new element to the file (appends to content for text files)."""
        if anchor_name is None or anchor_name == 'content':
            if before:
                self.source_code = new_code + self.source_code
            else:
                self.source_code = self.source_code + new_code
            self._parse_and_map(self.source_code)
            return True
        return False

    def delete_element(self, element_name: str) ->bool:
        """Deletes a named element from the file."""
        if element_name == 'content':
            self.source_code = ''
            self._parse_and_map('')
            return True
        return False

    def replace_partial(self, element_name: str, new_code: str, line_start:
        Optional[int]=None, line_end: Optional[int]=None, statement_index:
        Optional[int]=None) ->bool:
        """Replaces a specific part of an element's body."""
        if element_name != 'content':
            return False
        lines = self.source_code.splitlines()
        if line_start is not None and 1 <= line_start <= len(lines):
            start_idx = line_start - 1
            end_idx = start_idx if line_end is None else min(line_end - 1, 
                len(lines) - 1)
            new_lines = new_code.splitlines() if new_code else []
            lines[start_idx:end_idx + 1] = new_lines
            self.source_code = '\n'.join(lines)
            self._parse_and_map(self.source_code)
            return True
        return False

    def get_modified_source(self) ->str:
        """Returns the modified source code."""
        return self.source_code
