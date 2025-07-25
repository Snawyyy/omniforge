from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Union
from typing import List, Optional, Dict
ASTNode = Any
DiffContent = str


class ASTAdapter(ABC):
    """
    Abstract base class defining the interface for language-specific AST adapters.

    This interface allows the CodeEditor to interact with the AST/CST of different
    programming languages in a uniform way. Concrete implementations will handle
    the specifics of parsing, traversing, and modifying the AST/CST for their
    respective languages (e.g., Python's `ast`/`astor`, JavaScript's `tree-sitter`).

    The adapter is responsible for holding the parsed tree structure and any
    necessary metadata for operations.
    """

    def __init__(self, source_code: str):
        """
        Initializes the adapter by parsing the provided source code.

        Args:
            source_code: The string content of the source file to be parsed.

        Raises:
            ValueError: If the source code cannot be parsed due to syntax errors.
        """
        self.source_code: str = source_code
        self.tree: Optional[ASTNode] = None
        self.nodes: Dict[str, ASTNode] = {}
        self._parse_and_map(source_code)

    @abstractmethod
    def _parse_and_map(self, source_code: str) ->None:
        """
        Abstract method to parse the source code and populate `self.tree` and `self.nodes`.

        This is the core method where language-specific parsing logic resides.
        Implementations should:
        1. Parse the `source_code` into an AST/CST representation.
        2. Store the root of this representation in `self.tree`.
        3. Identify key top-level elements (functions, classes, variables, imports)
           and map their names to their nodes in `self.nodes`.

        Args:
            source_code: The string content to parse.

        Raises:
            ValueError: If the source code cannot be parsed.
        """
        pass

    @abstractmethod
    def list_elements(self) ->List[str]:
        """
        Abstract method to list the names of the main elements found in the code.

        These are typically top-level functions, classes, variable assignments,
        and imports that the adapter can identify and manipulate.

        Returns:
            A list of element names (strings).
        """
        pass

    @abstractmethod
    def get_source_of(self, element_name: str) ->Optional[str]:
        """
        Abstract method to get the source code string for a specific element.

        Args:
            element_name: The name of the element (function, class, etc.).

        Returns:
            The source code string for the element, or None if not found.
        """
        pass

    @abstractmethod
    def get_element_structure(self, element_name: str) ->Optional[Dict]:
        """
        Abstract method to get detailed structural information about an element.

        This information can include type, line numbers, body items, etc., useful
        for aiding the AI in understanding the code's layout.

        Args:
            element_name: The name of the element.

        Returns:
            A dictionary containing structural details, or None if not found.
            Example structure:
            {
                'name': 'func_name',
                'type': 'FunctionDef', # or 'ClassDef', etc.
                'line_start': 10,
                'line_end': 25,
                'body_items': [list of internal statement details...]
            }
        """
        pass

    @abstractmethod
    def get_element_body_snippet(self, element_name: str, line_start: int,
        line_end: int) ->Optional[str]:
        """
        Abstract method to extract a snippet of code from within an element's body.

        Used for 'partial' edits where only a specific range of lines within
        a function or class needs to be changed.

        Args:
            element_name: The name of the element containing the snippet.
            line_start: The starting line number (1-based, absolute) of the snippet.
            line_end: The ending line number (inclusive) of the snippet.

        Returns:
            The source code string for the specified lines within the element, or None.
        """
        pass

    @abstractmethod
    def replace_element(self, element_name: str, new_code: str) ->bool:
        """
        Abstract method to replace an entire named element.

        This involves finding the old element in the tree and swapping it with
        the representation of the `new_code`.

        Args:
            element_name: The name of the element to replace.
            new_code: The new source code for the element (and potential helpers).

        Returns:
            True if the replacement was successful, False otherwise.
        """
        pass

    @abstractmethod
    def add_element(self, new_code: str, anchor_name: Optional[str]=None,
        before: bool=False) ->bool:
        """
        Abstract method to add a new block of code (element) to the file.

        This involves parsing the `new_code` and inserting its representation
        into the tree at an appropriate location (e.g., end of file, near anchor).

        Args:
            new_code: The source code for the new element(s).
            anchor_name: Optional name of an existing element to position relative to.
            before: If True and `anchor_name` is provided, insert before the anchor.

        Returns:
            True if the element was added successfully, False otherwise.
        """
        pass

    @abstractmethod
    def delete_element(self, element_name: str) ->bool:
        """
        Abstract method to delete a named element from the file.

        This involves finding the element in the tree and removing its representation.

        Args:
            element_name: The name of the element to delete.

        Returns:
            True if the element was successfully deleted, False otherwise.
        """
        pass

    @abstractmethod
    def replace_partial(self, element_name: str, new_code: str, line_start:
        Optional[int]=None, line_end: Optional[int]=None, statement_index:
        Optional[int]=None) ->bool:
        """
        Abstract method for a 'surgical' edit within an element's body.

        Replaces a specific statement or line range within the body of an element.

        Args:
            element_name: Name of the function/class to modify.
            new_code: New code to insert (can be multiple statements).
            line_start: Starting line number (absolute) within the element.
            line_end: Ending line number (inclusive) within the element.
            statement_index: Alternative to line numbers - replace the Nth statement.

        Returns:
            True if successful, False otherwise.
        """
        pass

    @abstractmethod
    def get_modified_source(self) ->str:
        """
        Abstract method to serialize the potentially modified AST/CST back to source code.

        Returns:
            The full source code string reflecting the current state of the tree.
        """
        pass

    @abstractmethod
    def get_diff(self) ->str:
        """
        Abstract method to generate a diff between the original source and the modified source.

        Returns:
            A string containing the unified diff.
        """
        pass


"""
TextFileAdapter - Basic adapter for text files

This module provides a basic adapter for text files that implements
the ASTAdapter interface. It allows text files to be used with the
CodeEditor class.
"""


class TextFileAdapter(ASTAdapter):
    """
    A basic adapter for text files that implements the ASTAdapter interface.
    """

    def __init__(self, source_code: str):
        """
        Initializes the TextFileAdapter.

        Args:
            source_code: The source code as a string.
        """
        self.source_code = source_code
        self.modified_source = source_code

    def list_elements(self) ->List[str]:
        """
        Lists top-level elements in the text file.
        For text files, this returns a single "content" element.

        Returns:
            A list containing "content".
        """
        return ['content']

    def get_source_of(self, element_name: str) ->Optional[str]:
        """
        Gets the source code for a specific element.
        For text files, this returns the entire file content.

        Args:
            element_name: The name of the element.

        Returns:
            The source code of the entire file.
        """
        if element_name == 'content':
            return self.source_code
        return None

    def get_element_structure(self, element_name: str) ->Optional[Dict]:
        """
        Gets detailed structure information about an element.
        For text files, this provides minimal structure information.

        Args:
            element_name: The name of the element.

        Returns:
            A dictionary with basic structure information.
        """
        if element_name == 'content':
            lines = self.source_code.splitlines()
            return {'name': element_name, 'type': 'text', 'line_count': len
                (lines), 'character_count': len(self.source_code)}
        return None

    def get_element_body_snippet(self, element_name: str, line_start: int,
        line_end: int) ->Optional[str]:
        """
        Gets a snippet from within an element's body.
        For text files, this returns lines between line_start and line_end.

        Args:
            element_name: The name of the element.
            line_start: The starting line number (1-indexed).
            line_end: The ending line number (1-indexed).

        Returns:
            A string containing the specified lines.
        """
        if element_name != 'content':
            return None
        lines = self.source_code.splitlines()
        start_idx = max(0, line_start - 1)
        end_idx = min(len(lines), line_end)
        if start_idx >= len(lines) or start_idx >= end_idx:
            return None
        return '\n'.join(lines[start_idx:end_idx])

    def replace_partial(self, element_name: str, new_code: str, line_start:
        Optional[int]=None, line_end: Optional[int]=None, statement_index:
        Optional[int]=None) ->bool:
        """
        Replaces a partial section of an element.
        For text files, this replaces lines between line_start and line_end.

        Args:
            element_name: The name of the element.
            new_code: The new code to insert.
            line_start: The starting line number (1-indexed).
            line_end: The ending line number (1-indexed).
            statement_index: Not used for text files.

        Returns:
            True if the replacement was successful, False otherwise.
        """
        if element_name != 'content':
            return False
        if line_start is None or line_end is None:
            return False
        lines = self.modified_source.splitlines()
        start_idx = max(0, line_start - 1)
        end_idx = min(len(lines), line_end)
        if start_idx > len(lines) or start_idx > end_idx:
            return False
        new_lines = self.modified_source.splitlines()
        new_code_lines = new_code.splitlines()
        new_lines[start_idx:end_idx] = new_code_lines
        self.modified_source = '\n'.join(new_lines)
        return True

    def add_element(self, new_code: str, anchor_name: Optional[str]=None,
        before: bool=False) ->bool:
        """
        Adds new content to the text file.
        For text files, this appends or prepends content.

        Args:
            new_code: The new code to add.
            anchor_name: Not used for text files.
            before: If True, prepend; if False, append.

        Returns:
            True if the addition was successful, False otherwise.
        """
        if before:
            self.modified_source = new_code + '\n' + self.modified_source
        else:
            self.modified_source = self.modified_source + '\n' + new_code
        return True

    def delete_element(self, element_name: str) ->bool:
        """
        Deletes an element by name.
        For text files, this clears the entire content if element_name is "content".

        Args:
            element_name: The name of the element to delete.

        Returns:
            True if the deletion was successful, False otherwise.
        """
        if element_name == 'content':
            self.modified_source = ''
            return True
        return False

    def replace_element(self, element_name: str, new_code: str) ->bool:
        """
        Replaces a target element with new code.
        For text files, this replaces the entire content if element_name is "content".

        Args:
            element_name: The name of the element to replace.
            new_code: The new code.

        Returns:
            True if the replacement was successful, False otherwise.
        """
        if element_name == 'content':
            self.modified_source = new_code
            return True
        return False

    def get_modified_source(self) ->str:
        """
        Gets the modified source code.

        Returns:
            The modified source code.
        """
        return self.modified_source

    def get_diff(self) ->str:
        """
        Generates a diff between the original source and the modified source.

        Returns:
            A string containing the diff.
        """
        import difflib
        return ''.join(difflib.unified_diff(self.source_code.splitlines(
            keepends=True), self.modified_source.splitlines(keepends=True),
            fromfile='original', tofile='modified'))
