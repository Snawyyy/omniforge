# python_ast_adapter.py

"""
PythonASTAdapter - Concrete AST adapter for Python using built-in `ast` and `astor`.

This module implements the ASTAdapter interface specifically for Python,
leveraging the standard library's `ast` module for parsing and
manipulation, and `astor` for code generation.
"""

import ast
import astor
import difflib
from typing import List, Optional, Dict, Tuple, Union
from ast_adapter import ASTAdapter

# Optional dependency check for asttokens (for enhanced partial edits)
try:
    import asttokens
    ASTTOKENS_AVAILABLE = True
except ImportError:
    ASTTOKENS_AVAILABLE = False
    # print("Warning: asttokens not installed. Partial edits will be limited.")


class PythonASTAdapter(ASTAdapter):
    """
    Concrete implementation of ASTAdapter for Python source code.

    This adapter uses Python's built-in `ast` module to parse and manipulate
    the code, and `astor` for code generation and source-to-source transformations.
    It holds the parsed AST tree and provides methods to interact with it
    according to the ASTAdapter interface.
    """

    def __init__(self, source_code: str):
        """
        Initializes the PythonASTAdapter by parsing the source code.

        Args:
            source_code: The Python source code as a string.
        """
        # Store source code for diffing and potential asttokens use
        self.source_code: str = source_code
        # Will hold the parsed AST tree
        self.tree: Optional[ast.AST] = None
        # Will hold a mapping of element names to their AST nodes
        self.nodes: Dict[str, ast.AST] = {}
        # asttokens instance for enhanced source mapping (if available)
        self.atok: Optional[asttokens.ASTTokens] = None

        # Call the parent's __init__ which in turn calls _parse_and_map
        super().__init__(source_code)

    def _parse_and_map(self, source_code: str) -> None:
        """
        Parses the Python source code and maps elements.

        Args:
            source_code: The Python source code string to parse.

        Raises:
            ValueError: If the source code has invalid Python syntax.
        """
        try:
            self.tree = ast.parse(source_code)
        except SyntaxError as e:
            raise ValueError(f"Invalid Python syntax: {e}") from e

        self.nodes = self._map_nodes()
        if ASTTOKENS_AVAILABLE:
            try:
                self.atok = asttokens.ASTTokens(source_code, parse=True)
            except Exception:
                # If asttokens fails for any reason, continue without it
                self.atok = None
        else:
            self.atok = None

    def _map_nodes(self) -> Dict[str, ast.AST]:
        """
        Walks the AST and creates a map of element names to nodes.

        Returns:
            A dictionary mapping element names (str) to their AST nodes.
        """
        nodes: Dict[str, ast.AST] = {}
        if not self.tree:
            return nodes # Return empty dict if no tree

        for node in ast.walk(self.tree):
            # Map functions and classes by name
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                # Use 'not in' to prioritize top-level definitions in case of conflicts
                if node.name not in nodes:
                    nodes[node.name] = node
            # Map assignments by target variable name(s)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id not in nodes:
                        nodes[target.id] = node
            # Map imports by their alias or original name
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name
                    if name not in nodes:
                        nodes[name] = node
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname or alias.name
                    if name not in nodes:
                        nodes[name] = node
        return nodes

    def _find_statement_in_body(self, body: List[ast.AST], line_start: int, line_end: Optional[int] = None) -> Optional[Tuple[int, ast.AST]]:
        """
        Finds a statement within a body based on line numbers.

        Args:
            body: The list of AST nodes representing the body.
            line_start: The starting line number to search for.
            line_end: The optional ending line number.

        Returns:
            A tuple of (index, statement node) if found, otherwise None.
        """
        for i, stmt in enumerate(body):
            if hasattr(stmt, 'lineno'):
                if line_end:
                    stmt_end = getattr(stmt, 'end_lineno', stmt.lineno)
                    # Check for overlap or containment
                    if (stmt.lineno <= line_start <= stmt_end) or (stmt.lineno <= line_end <= stmt_end) or \
                       (line_start <= stmt.lineno and line_end >= stmt_end):
                        return (i, stmt)
                else:
                    if stmt.lineno == line_start:
                        return (i, stmt)
        return None

    def _add_imports(self, new_import_nodes: List[Union[ast.Import, ast.ImportFrom]]) -> None:
        """
        Adds new import nodes to the file's AST, typically at the top.

        Args:
            new_import_nodes: A list of ast.Import or ast.ImportFrom nodes.
        """
        if not self.tree or not hasattr(self.tree, 'body'):
            return # Cannot add imports without a valid module tree

        # Get string representations of existing imports to avoid duplicates
        existing_imports_str = set()
        last_import_index = -1
        for i, node in enumerate(self.tree.body):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                try:
                    existing_imports_str.add(astor.to_source(node).strip())
                except Exception:
                    # If astor fails, skip adding to set (might lead to potential duplicate, but safer)
                    pass
                last_import_index = i

        # Insert new imports after the last existing import
        # Reverse them so they are inserted in the correct order
        for new_import in reversed(new_import_nodes):
            try:
                new_import_str = astor.to_source(new_import).strip()
                if new_import_str not in existing_imports_str:
                    self.tree.body.insert(last_import_index + 1, new_import)
                    last_import_index += 1 # Update index for next insertion
            except Exception:
                # If we can't generate source, we can't check for duplicates, skip
                self.tree.body.insert(last_import_index + 1, new_import)
                last_import_index += 1

    # --- Implementing abstract methods from ASTAdapter ---

    def list_elements(self) -> List[str]:
        """Lists the names of the main top-level elements."""
        return list(self.nodes.keys())

    def get_source_of(self, element_name: str) -> Optional[str]:
        """Gets the source code string for a specific named element."""
        node = self.nodes.get(element_name)
        if node:
            try:
                return astor.to_source(node)
            except Exception:
                # Handle potential astor issues gracefully
                return None
        return None

    def get_element_structure(self, element_name: str) -> Optional[Dict]:
        """Gets detailed structural information about an element."""
        node = self.nodes.get(element_name)
        if not node:
            return None

        structure = {
            'name': element_name,
            'type': node.__class__.__name__,
            'line_start': getattr(node, 'lineno', None),
            'line_end': getattr(node, 'end_lineno', None),
            'body_items': []
        }

        if hasattr(node, 'body'):
            for i, item in enumerate(node.body):
                item_info = {
                    'index': i,
                    'type': item.__class__.__name__,
                    'line_start': getattr(item, 'lineno', None),
                    'line_end': getattr(item, 'end_lineno', None)
                }

                if isinstance(item, ast.Assign) and item.targets:
                    target = item.targets[0]
                    if isinstance(target, ast.Name):
                        item_info['assigns'] = target.id
                elif isinstance(item, (ast.If, ast.While, ast.For)):
                    item_info['has_body'] = bool(getattr(item, 'body', None))
                elif isinstance(item, ast.Return):
                    item_info['returns'] = True

                structure['body_items'].append(item_info)

        return structure

    def get_element_body_snippet(self, element_name: str, line_start: int, line_end: int) -> Optional[str]:
        """Extracts a snippet of code from within an element's body."""
        if not self.atok:
            return None # asttokens is required for precise original source retrieval

        node = self.nodes.get(element_name)
        if not node or not hasattr(node, 'body'):
            return None

        statements = []
        for stmt in node.body:
            if hasattr(stmt, 'lineno') and hasattr(stmt, 'end_lineno'):
                 # Check for overlap or containment of the statement within the requested range
                stmt_start = stmt.lineno
                stmt_end = stmt.end_lineno
                if (stmt_start >= line_start and stmt_end <= line_end) or \
                   (stmt_start <= line_end and stmt_end >= line_start): # Overlap
                    statements.append(stmt)

        if not statements:
            return None

        # Use asttokens to get the original source text for accuracy
        try:
            # Combine text ranges of the found statements
            combined_text = ""
            last_end_pos = None
            for stmt in sorted(statements, key=lambda s: s.lineno):
                # Get the text range for the statement
                stmt_text = self.atok.get_text_range(stmt)
                if last_end_pos is not None and stmt_text[0] > last_end_pos:
                     # Add the original whitespace/newlines between statements
                    combined_text += self.source_code[last_end_pos:stmt_text[0]]
                combined_text += self.atok.get_text(stmt)
                last_end_pos = stmt_text[1]
            return combined_text.strip()
        except Exception:
            # Fallback if asttokens text retrieval fails
            return '\n'.join(astor.to_source(stmt).strip() for stmt in statements)

    def replace_element(self, element_name: str, new_code: str) -> bool:
        """Replaces a named element with new code."""
        if element_name not in self.nodes or not self.tree:
            return False

        try:
            new_ast_module = ast.parse(new_code)
        except SyntaxError:
            return False

        new_imports = [n for n in new_ast_module.body if isinstance(n, (ast.Import, ast.ImportFrom))]
        new_code_body = [n for n in new_ast_module.body if not isinstance(n, (ast.Import, ast.ImportFrom))]

        if not new_code_body: # Ensure there's actual code body to replace with
            return False

        if new_imports:
            self._add_imports(new_imports)

        # Walk the tree to find the parent node containing the element to replace
        for parent_node in ast.walk(self.tree):
            if hasattr(parent_node, 'body') and isinstance(parent_node.body, list):
                try:
                    old_node = self.nodes[element_name]
                    idx = parent_node.body.index(old_node)
                    # Remove the old node
                    parent_node.body.pop(idx)
                    # Insert the new nodes
                    for i, new_node in enumerate(new_code_body):
                        parent_node.body.insert(idx + i, new_node)

                    # Update the nodes map: remove old, add new top-level definitions
                    del self.nodes[element_name]
                    for n in new_code_body:
                        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                            self.nodes[n.name] = n
                    return True
                except (ValueError, KeyError):
                    # ValueError from index(), KeyError from accessing self.nodes
                    continue
        return False # Element not found in any body

    def add_element(self, new_code: str, anchor_name: Optional[str] = None, before: bool = False) -> bool:
        """Adds a new element to the file."""
        if not self.tree or not hasattr(self.tree, 'body'):
             return False

        try:
            new_ast_module = ast.parse(new_code)
        except (SyntaxError, IndexError):
            return False

        new_imports = [n for n in new_ast_module.body if isinstance(n, (ast.Import, ast.ImportFrom))]
        new_code_body = [n for n in new_ast_module.body if not isinstance(n, (ast.Import, ast.ImportFrom))]

        if not new_code_body:
            return False

        if new_imports:
            self._add_imports(new_imports)

        # --- Determine insertion index ---

        # Find the `if __name__ == "__main__":` block index
        main_block_idx = -1
        for i, node in enumerate(self.tree.body):
            if (isinstance(node, ast.If) and
                isinstance(getattr(node, 'test', None), ast.Compare) and
                isinstance(getattr(node.test, 'left', None), ast.Name) and
                node.test.left.id == '__name__' and
                len(getattr(node.test, 'ops', [])) == 1 and isinstance(node.test.ops[0], ast.Eq) and
                len(getattr(node.test, 'comparators', [])) == 1):

                comp = node.test.comparators[0]
                # Check for both ast.Constant ('__main__') and older ast.Str ('__main__')
                if ((isinstance(comp, ast.Constant) and comp.value == '__main__') or
                    (isinstance(comp, ast.Str) and comp.s == '__main__')): # type: ignore
                    main_block_idx = i
                    break

        insertion_index = -1
        if anchor_name:
            # If anchor is specified, find its index
            if anchor_name not in self.nodes:
                return False
            anchor_node = self.nodes[anchor_name]
            try:
                anchor_idx = self.tree.body.index(anchor_node)
                proposed_index = anchor_idx if before else anchor_idx + 1
                # Prefer to stay before the main block if possible
                if main_block_idx != -1:
                    insertion_index = min(proposed_index, main_block_idx)
                else:
                    insertion_index = proposed_index
            except ValueError:
                return False # Anchor node not found in tree body
        elif main_block_idx != -1:
            # If no anchor, but there's a main block, insert before it
            insertion_index = main_block_idx
        # If no anchor and no main block, insertion_index remains -1

        # --- Perform the insertion ---
        if insertion_index == -1:
            # Append to the end
            self.tree.body.extend(new_code_body)
        else:
            # Insert at the calculated position
            for i, new_node in enumerate(new_code_body):
                self.tree.body.insert(insertion_index + i, new_node)

        # Update the nodes map with any new top-level definitions
        for node in new_code_body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                self.nodes[node.name] = node # This might overwrite if names clash

        return True

    def delete_element(self, element_name: str) -> bool:
        """Deletes a named element from the file."""
        if not self.tree or not hasattr(self.tree, 'body'):
            return False

        deleted = False
        if element_name in self.nodes:
            node_to_delete = self.nodes[element_name]
            # Walk the tree to find the parent node containing the element
            for node in ast.walk(self.tree):
                if hasattr(node, 'body') and isinstance(node.body, list):
                    try:
                        node.body.remove(node_to_delete)
                        deleted = True
                        break # Assume element appears only once at top level
                    except ValueError:
                        continue # This parent doesn't contain the node
            if deleted:
                del self.nodes[element_name]
                # Although nodes map is passed by ref in base __init__, we should call _map_nodes
                # to ensure consistency after a direct tree modification.
                self.nodes = self._map_nodes()
                return True

        # If not found by node reference, try to find by name pattern matching (vars/imports)
        new_body = []
        for node in self.tree.body:
            if isinstance(node, ast.Assign):
                match = False
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == element_name:
                        match = True
                        deleted = True
                        break
                if not match: # Keep the node if it doesn't match
                    new_body.append(node)
            elif isinstance(node, ast.Import):
                new_aliases = [alias for alias in node.names if not ((alias.name == element_name) or (alias.asname == element_name))]
                if new_aliases:
                    node.names = new_aliases
                    new_body.append(node)
                elif not any((alias.name == element_name) or (alias.asname == element_name) for alias in node.names):
                    # Keep the node if none of its aliases match (should theoretically be the same as above)
                     new_body.append(node)
                else:
                    deleted = True # The import node is being completely removed
            elif isinstance(node, ast.ImportFrom):
                new_aliases = [alias for alias in node.names if not ((alias.name == element_name) or (alias.asname == element_name))]
                if new_aliases:
                    node.names = new_aliases
                    new_body.append(node)
                elif not any((alias.name == element_name) or (alias.asname == element_name) for alias in node.names):
                     new_body.append(node)
                else:
                    deleted = True
            else:
                new_body.append(node)

        if deleted:
            self.tree.body = new_body
            # Remap nodes after structural changes
            self.nodes = self._map_nodes()

        return deleted

    def replace_partial(self, element_name: str, new_code: str,
                       line_start: Optional[int] = None, line_end: Optional[int] = None,
                       statement_index: Optional[int] = None) -> bool:
        """Replaces a specific part of an element's body."""
        if element_name not in self.nodes:
            return False

        node = self.nodes[element_name]
        # Ensure the node has a body to modify
        if not hasattr(node, 'body') or not isinstance(node.body, list):
            return False

        # Parse the new code to get AST nodes for the replacement
        try:
             # Heuristic: If new code looks like a def/class, extract its body.
             # Otherwise, treat as standalone statements.
            if new_code.strip().startswith(('def ', 'class ', 'async def ')):
                # Parse as if it's a module with a single function/class
                temp_module = ast.parse(new_code)
                if temp_module.body and hasattr(temp_module.body[0], 'body'):
                    new_statements = temp_module.body[0].body # Get the inner body
                else:
                    return False # Malformed attempt to define a func/class
            else:
                # Parse as a module and take its body
                new_ast_module = ast.parse(new_code)
                new_statements = new_ast_module.body
        except SyntaxError:
            return False # Invalid new code

        if not new_statements: # Nothing to insert
            return False

        # --- Determine what to replace based on parameters ---
        if statement_index is not None:
            # Replace by statement index
            if 0 <= statement_index < len(node.body):
                # Replace the single statement at index with the list of new statements
                node.body[statement_index:statement_index+1] = new_statements
                return True
        elif line_start is not None:
            # Replace by line number(s)
            result = self._find_statement_in_body(node.body, line_start, line_end)
            if result:
                idx, _ = result
                if line_end:
                    # Find the last statement within the specified range to replace multiple
                    end_idx = idx
                    # Iterate from the found index forward
                    for i in range(idx, len(node.body)):
                        stmt = node.body[i]
                        stmt_s_ln = getattr(stmt, 'lineno', None)
                        stmt_e_ln = getattr(stmt, 'end_lineno', stmt_s_ln)
                        if stmt_s_ln is not None and stmt_e_ln is not None:
                            # Check if the statement ends within the range or starts within the range
                            # This handles overlapping ranges correctly
                             if stmt_e_ln <= line_end or stmt_s_ln <= line_end:
                                 end_idx = i
                             else:
                                 break # Statement is past the end range
                        else:
                            break # Can't determine statement range
                    node.body[idx:end_idx+1] = new_statements
                else:
                    # line_end not specified, only replace the statement at line_start
                    node.body[idx:idx+1] = new_statements
                return True

        # If none of the conditions were met to perform a replacement
        return False

    def get_modified_source(self) -> str:
        """Serializes the modified AST back into source code."""
        if self.tree:
            try:
                return astor.to_source(self.tree)
            except Exception as e:
                 # Fallback error handling, should ideally not happen if tree is valid
                 return f"# Error generating source: {e}\n{self.source_code}"
        else:
            # If somehow the tree is None, return the original source
            return self.source_code

    def get_diff(self) -> str:
        """Generates a diff between the original and modified source code."""
        modified_source = self.get_modified_source()
        # Ensure line endings are consistent for diffing, keepends=True preserves them
        # If source_code had different line endings, this might still cause issues,
        # but this is a standard approach.
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