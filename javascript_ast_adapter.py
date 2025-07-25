# javascript_ast_adapter.py

"""
JavaScriptASTAdapter - Concrete AST adapter for JavaScript using tree-sitter.

This module implements the ASTAdapter interface specifically for JavaScript,
leveraging the tree-sitter library for parsing and manipulation.
"""

import difflib
from typing import List, Optional, Dict, Any, Tuple
from ast_adapter import ASTAdapter

# Optional dependency check for tree-sitter
try:
    import tree_sitter
    import tree_sitter_languages
    TREETSITTER_AVAILABLE = True
except ImportError:
    TREETSITTER_AVAILABLE = False
    # This will cause an error during initialization if the adapter is used


class JavaScriptASTAdapter(ASTAdapter):
    """
    Concrete implementation of ASTAdapter for JavaScript source code.

    This adapter uses tree-sitter to parse and manipulate JavaScript code.
    It holds the parsed tree-sitter Tree and provides methods to interact
    with it according to the ASTAdapter interface.
    """

    def __init__(self, source_code: str):
        """
        Initializes the JavaScriptASTAdapter by parsing the source code.

        Args:
            source_code: The JavaScript source code as a string.

        Raises:
            ValueError: If tree-sitter libraries are not available or if
                        the source code has invalid JavaScript syntax.
        """
        if not TREETSITTER_AVAILABLE:
            raise ValueError("tree-sitter and tree-sitter-languages are required for JavaScript support.")
            
        # Store source code for diffing and manipulation
        self.source_code: str = source_code
        # Will hold the parsed tree-sitter tree
        self.tree: Optional[tree_sitter.Tree] = None
        # Will hold a mapping of element names to their tree-sitter nodes
        self.nodes: Dict[str, tree_sitter.Node] = {}
        # Tree-sitter language parser
        self.language = tree_sitter_languages.get_language("javascript")
        self.parser = tree_sitter.Parser(self.language)

        # Call the parent's __init__ which in turn calls _parse_and_map
        super().__init__(source_code)

    def _parse_and_map(self, source_code: str) -> None:
        """
        Parses the JavaScript source code and maps elements.

        Args:
            source_code: The JavaScript source code string to parse.

        Raises:
            ValueError: If the source code has invalid JavaScript syntax.
        """
        try:
            # Encode the source code in bytes as required by tree-sitter
            self.tree = self.parser.parse(bytes(source_code, "utf-8"))
        except Exception as e:
            raise ValueError(f"Failed to parse JavaScript source: {e}") from e

        self.nodes = self._map_nodes()

    def _map_nodes(self) -> Dict[str, tree_sitter.Node]:
        """
        Walks the tree and creates a map of element names to nodes.

        Returns:
            A dictionary mapping element names (str) to their tree-sitter nodes.
        """
        nodes: Dict[str, tree_sitter.Node] = {}
        if not self.tree:
            return nodes # Return empty dict if no tree

        # Define the types of nodes we're interested in
        target_types = {
            "function_declaration", "class_declaration", 
            "variable_declarator", "import_statement"
        }
        
        # Walk the tree using a stack-based approach
        stack = [self.tree.root_node]
        while stack:
            node = stack.pop()
            
            # Check if this is a target node type
            if node.type in target_types:
                # Extract the name for different node types
                name = self._get_node_name(node)
                if name and name not in nodes:
                    nodes[name] = node
            
            # Add children to the stack for further processing
            for child in reversed(node.children):  # Reverse to maintain order when popping
                stack.append(child)
                
        return nodes
    
    def _get_node_name(self, node: tree_sitter.Node) -> Optional[str]:
        """
        Extracts the name of a node based on its type.
        
        Args:
            node: The tree-sitter node to extract the name from.
            
        Returns:
            The name of the node, or None if no name could be found.
        """
        if node.type == "function_declaration":
            # Find the identifier child
            for child in node.children:
                if child.type == "identifier":
                    return child.text.decode("utf-8")
        elif node.type == "class_declaration":
            # Find the identifier child
            for child in node.children:
                if child.type == "identifier":
                    return child.text.decode("utf-8")
        elif node.type == "variable_declarator":
            # Find the identifier child
            for child in node.children:
                if child.type == "identifier":
                    return child.text.decode("utf-8")
        elif node.type == "import_statement":
            # This is a more complex case - for now, we'll use a simplified approach
            # Extract the module name from the import statement
            # e.g., in "import foo from 'bar'", we want "foo"
            # This is a simplified implementation and might need refinement
            import_clause = None
            for child in node.children:
                if child.type == "import_clause":
                    import_clause = child
                    break
            
            if import_clause:
                # Check for a simple identifier
                for child in import_clause.children:
                    if child.type == "identifier":
                        return child.text.decode("utf-8")
                    elif child.type == "named_imports":
                        # Handle named imports like { foo, bar }
                        # For simplicity, we'll just return a placeholder
                        # A more complete implementation would extract all names
                        return f"import_from_{hash(node.text.decode('utf-8')) % 10000}"
        
        return None

    def _find_node_by_position(self, start_point: Tuple[int, int], 
                              end_point: Optional[Tuple[int, int]] = None) -> Optional[tree_sitter.Node]:
        """
        Finds a node in the tree that corresponds to a given range.
        
        Args:
            start_point: A (row, column) tuple indicating the start position.
            end_point: A (row, column) tuple indicating the end position.
            
        Returns:
            The tree-sitter node that corresponds to the range, or None if not found.
        """
        if not self.tree:
            return None
            
        # A simple approach: find the smallest node that contains the range
        # This is a simplified implementation and might need refinement
        def contains_range(node):
            node_start = (node.start_point[0], node.start_point[1])
            node_end = (node.end_point[0], node.end_point[1])
            if end_point:
                return (node_start <= start_point and node_end >= end_point)
            else:
                return node_start <= start_point <= node_end
        
        # Walk the tree to find matching nodes
        stack = [self.tree.root_node]
        candidates = []
        
        while stack:
            current_node = stack.pop()
            if contains_range(current_node):
                candidates.append(current_node)
                # Add children to continue searching for smaller nodes
                stack.extend(current_node.children)
        
        # Return the smallest (last) candidate
        return candidates[-1] if candidates else None
    
    def _get_line_info_from_point(self, point: Tuple[int, int]) -> Dict[str, Any]:
        """
        Converts a tree-sitter point to line information.
        
        Args:
            point: A (row, column) tuple from tree-sitter.
            
        Returns:
            A dictionary with line_start and line_end information.
        """
        # Tree-sitter uses 0-based indexing for rows
        return {
            'line_start': point[0] + 1,  # Convert to 1-based
            'line_end': point[0] + 1
        }

    def _reparse_tree(self, new_source: str) -> None:
        """
        Re-parses the tree with new source code.
        
        This is necessary because tree-sitter trees are immutable.
        
        Args:
            new_source: The new source code to parse.
        """
        self.source_code = new_source
        self.tree = self.parser.parse(bytes(new_source, "utf-8"))
        self.nodes = self._map_nodes()

    # --- Implementing abstract methods from ASTAdapter ---

    def list_elements(self) -> List[str]:
        """Lists the names of the main top-level elements."""
        return list(self.nodes.keys())

    def get_source_of(self, element_name: str) -> Optional[str]:
        """Gets the source code string for a specific named element."""
        node = self.nodes.get(element_name)
        if node:
            try:
                return node.text.decode("utf-8")
            except Exception:
                # Handle potential decoding issues gracefully
                return None
        return None

    def get_element_structure(self, element_name: str) -> Optional[Dict]:
        """Gets detailed structural information about an element."""
        node = self.nodes.get(element_name)
        if not node:
            return None

        structure = {
            'name': element_name,
            'type': node.type,
            'line_start': node.start_point[0] + 1,  # Convert to 1-based
            'line_end': node.end_point[0] + 1,
            'body_items': []
        }

        # Add body items for functions and classes
        if node.type in ("function_declaration", "class_declaration"):
            # Find the body block
            body_node = None
            for child in node.children:
                if child.type == "statement_block":
                    body_node = child
                    break
            
            if body_node:
                # Process statements in the body
                for i, item in enumerate(body_node.children):
                    # Skip '{' and '}' tokens
                    if item.type in ("{", "}"):
                        continue
                    
                    item_info = {
                        'index': i,
                        'type': item.type,
                        'line_start': item.start_point[0] + 1,
                        'line_end': item.end_point[0] + 1
                    }
                    
                    # Add more specific information based on type
                    if item.type == "variable_declaration":
                        item_info['declares'] = "variable"
                    elif item.type == "return_statement":
                        item_info['returns'] = True
                    elif item.type in ("if_statement", "for_statement", "while_statement"):
                        item_info['has_body'] = True
                    
                    structure['body_items'].append(item_info)

        return structure

    def get_element_body_snippet(self, element_name: str, line_start: int, line_end: int) -> Optional[str]:
        """Extracts a snippet of code from within an element's body."""
        node = self.nodes.get(element_name)
        if not node:
            return None
            
        # A simplified approach to extracting a snippet by line numbers
        # This would need to be more sophisticated for production use
        source_lines = self.source_code.split('\n')
        # Adjust for 0-based indexing
        start_idx = max(0, line_start - 1)
        end_idx = min(len(source_lines), line_end)
        
        if start_idx < end_idx:
            return '\n'.join(source_lines[start_idx:end_idx])
        
        return None

    def replace_element(self, element_name: str, new_code: str) -> bool:
        """Replaces a named element with new code."""
        if element_name not in self.nodes or not self.tree:
            return False

        node = self.nodes[element_name]
        
        # Get the start and end bytes of the node
        start_byte = node.start_byte
        end_byte = node.end_byte
        
        # Replace the node's text in the source code
        new_source = self.source_code[:start_byte] + new_code + self.source_code[end_byte:]
        
        # Re-parse the tree with the new source
        try:
            self._reparse_tree(new_source)
            return True
        except Exception:
            # If parsing fails, revert to the original source
            try:
                self._reparse_tree(self.source_code)
            except Exception:
                pass  # If we can't even re-parse the original, we're in trouble
            return False

    def add_element(self, new_code: str, anchor_name: Optional[str] = None, before: bool = False) -> bool:
        """Adds a new element to the file."""
        if not self.tree:
            return False
            
        # For simplicity, we'll add the new code at the end of the file
        # A more sophisticated implementation would handle the anchor and positioning
        new_source = self.source_code.rstrip() + "\n\n" + new_code + "\n"
        
        # Re-parse the tree with the new source
        try:
            self._reparse_tree(new_source)
            return True
        except Exception:
            # If parsing fails, revert to the original source
            try:
                self._reparse_tree(self.source_code)
            except Exception:
                pass
            return False

    def delete_element(self, element_name: str) -> bool:
        """Deletes a named element from the file."""
        if element_name not in self.nodes or not self.tree:
            return False

        node = self.nodes[element_name]
        
        # Find the full lines that contain the node
        # This is a simplified approach to avoid leaving partial lines
        source_lines = self.source_code.split('\n')
        start_line = node.start_point[0]
        end_line = node.end_point[0]
        
        # Create new source without those lines
        new_lines = source_lines[:start_line] + source_lines[end_line+1:]
        new_source = '\n'.join(new_lines)
        
        # Re-parse the tree with the new source
        try:
            self._reparse_tree(new_source)
            return True
        except Exception:
            # If parsing fails, revert to the original source
            try:
                self._reparse_tree(self.source_code)
            except Exception:
                pass
            return False

    def replace_partial(self, element_name: str, new_code: str,
                       line_start: Optional[int] = None, line_end: Optional[int] = None,
                       statement_index: Optional[int] = None) -> bool:
        """Replaces a specific part of an element's body."""
        # This is a complex operation that would require more sophisticated
        # tree navigation and manipulation than what's shown here.
        # For now, we'll provide a basic implementation.
        
        node = self.nodes.get(element_name)
        if not node:
            return False
            
        # Handle line-based replacement
        if line_start is not None:
            # Convert to 0-based indexing
            start_idx = max(0, line_start - 1)
            end_idx = line_end if line_end is not None else start_idx + 1
            
            source_lines = self.source_code.split('\n')
            if start_idx < len(source_lines):
                # Replace the specified lines
                end_idx = min(end_idx, len(source_lines))
                new_lines = source_lines[:start_idx] + [new_code] + source_lines[end_idx:]
                new_source = '\n'.join(new_lines)
                
                # Re-parse the tree with the new source
                try:
                    self._reparse_tree(new_source)
                    return True
                except Exception:
                    # If parsing fails, revert to the original source
                    try:
                        self._reparse_tree(self.source_code)
                    except Exception:
                        pass
        
        return False

    def get_modified_source(self) -> str:
        """Serializes the modified AST back into source code."""
        # For tree-sitter, the source code is already maintained separately
        return self.source_code

    def get_diff(self) -> str:
        """Generates a diff between the original and modified source code."""
        modified_source = self.get_modified_source()
        
        # Ensure line endings are consistent for diffing
        original_lines = self.source_code.splitlines(keepends=True)
        modified_lines = modified_source.splitlines(keepends=True)

        # Avoid diff header if contents are identical
        if original_lines == modified_lines:
            return ""

        diff = difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile='original',
            tofile='modified'
        )
        # Join the diff generator into a single string
        return ''.join(diff)