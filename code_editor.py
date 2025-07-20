"""
CodeEditor - Enhanced AST-based Python code manipulation tool

This module provides a class to programmatically parse, analyze,
and edit Python source code using Abstract Syntax Trees (AST).
It supports both full element replacement and surgical partial edits
within functions and classes using asttokens for precise source mapping.
"""
import ast
import astor
import difflib
from typing import List, Optional, Dict, Union, Tuple
try:
    import asttokens
    ASTTOKENS_AVAILABLE = True
except ImportError:
    ASTTOKENS_AVAILABLE = False
    print("Warning: asttokens not installed. Partial edits will be limited.")


class CodeEditor:
    """An enhanced class to safely edit Python files using AST with partial edit support."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.source_code = self._read_file()
        self.tree: ast.AST = self._parse_source()
        self.nodes: Dict[str, ast.AST] = self._map_nodes()
        # Enhanced source tracking with asttokens
        if ASTTOKENS_AVAILABLE:
            self.atok = asttokens.ASTTokens(self.source_code, parse=True)
        else:
            self.atok = None

    def _read_file(self) -> str:
        try:
            with open(self.file_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            raise ValueError(f'File not found: {self.file_path}')

    def _parse_source(self) -> ast.AST:
        try:
            return ast.parse(self.source_code)
        except SyntaxError as e:
            raise ValueError(f'Invalid Python syntax in {self.file_path}: {e}')

    def _map_nodes(self) -> Dict[str, ast.AST]:
        nodes = {}
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name not in nodes:
                    nodes[node.name] = node
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id not in nodes:
                        nodes[target.id] = node
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

    def list_elements(self) -> List[str]:
        return list(self.nodes.keys())

    def get_source_of(self, element_name: str) -> Optional[str]:
        node = self.nodes.get(element_name)
        return astor.to_source(node) if node else None

    def get_element_structure(self, element_name: str) -> Optional[Dict]:
        """
        Get detailed structure information about an element including
        line numbers and internal components.
        """
        node = self.nodes.get(element_name)
        if not node:
            return None
        
        structure = {
            'name': element_name,
            'type': node.__class__.__name__,
            'line_start': node.lineno if hasattr(node, 'lineno') else None,
            'line_end': node.end_lineno if hasattr(node, 'end_lineno') else None,
            'body_items': []
        }
        
        if hasattr(node, 'body'):
            for i, item in enumerate(node.body):
                item_info = {
                    'index': i,
                    'type': item.__class__.__name__,
                    'line_start': item.lineno if hasattr(item, 'lineno') else None,
                    'line_end': item.end_lineno if hasattr(item, 'end_lineno') else None
                }
                
                # Add more details for common statement types
                if isinstance(item, ast.Assign) and item.targets:
                    target = item.targets[0]
                    if isinstance(target, ast.Name):
                        item_info['assigns'] = target.id
                elif isinstance(item, (ast.If, ast.While, ast.For)):
                    item_info['has_body'] = bool(item.body)
                elif isinstance(item, ast.Return):
                    item_info['returns'] = True
                    
                structure['body_items'].append(item_info)
                
        return structure

    def _find_statement_in_body(self, body: List[ast.AST], line_start: int, line_end: Optional[int] = None) -> Optional[Tuple[int, ast.AST]]:
        """
        Find a statement in a body by line number range.
        Returns (index, statement) or None.
        """
        for i, stmt in enumerate(body):
            if hasattr(stmt, 'lineno'):
                if line_end:
                    stmt_end = stmt.end_lineno if hasattr(stmt, 'end_lineno') else stmt.lineno
                    if stmt.lineno <= line_start <= stmt_end or stmt.lineno <= line_end <= stmt_end:
                        return (i, stmt)
                else:
                    if stmt.lineno == line_start:
                        return (i, stmt)
        return None

    def replace_partial(self, element_name: str, new_code: str, 
                       line_start: Optional[int] = None, line_end: Optional[int] = None,
                       statement_index: Optional[int] = None) -> bool:
        """
        Replace a partial section of an element (function/class).
        
        Args:
            element_name: Name of the function/class to modify
            new_code: New code to insert (can be multiple statements)
            line_start: Starting line number within the element (1-based, absolute)
            line_end: Ending line number within the element (inclusive)
            statement_index: Alternative to line numbers - replace the Nth statement
            
        Returns:
            True if successful, False otherwise
        """
        if element_name not in self.nodes:
            return False
            
        node = self.nodes[element_name]
        if not hasattr(node, 'body') or not isinstance(node.body, list):
            return False
            
        try:
            # Parse the new code
            if new_code.strip().startswith('def ') or new_code.strip().startswith('class '):
                # If it's a full function/class, extract just the body
                new_ast = ast.parse(new_code)
                new_statements = new_ast.body[0].body
            else:
                # Parse as a module and get all statements
                new_ast = ast.parse(new_code)
                new_statements = new_ast.body
        except SyntaxError:
            return False
            
        if not new_statements:
            return False
            
        # Find what to replace
        if statement_index is not None:
            # Replace by index
            if 0 <= statement_index < len(node.body):
                node.body[statement_index:statement_index+1] = new_statements
                return True
        elif line_start is not None:
            # Replace by line number
            result = self._find_statement_in_body(node.body, line_start, line_end)
            if result:
                idx, _ = result
                if line_end:
                    # Find end index
                    end_idx = idx
                    for i in range(idx + 1, len(node.body)):
                        stmt = node.body[i]
                        if hasattr(stmt, 'end_lineno') and stmt.end_lineno <= line_end:
                            end_idx = i
                        else:
                            break
                    node.body[idx:end_idx+1] = new_statements
                else:
                    node.body[idx:idx+1] = new_statements
                return True
                
        return False

    def insert_in_element(self, element_name: str, new_code: str, 
                         position: str = 'end', 
                         after_line: Optional[int] = None,
                         before_line: Optional[int] = None) -> bool:
        """
        Insert new code into an element without replacing existing code.
        
        Args:
            element_name: Name of the function/class
            new_code: Code to insert
            position: 'start', 'end', or use after_line/before_line
            after_line: Insert after this line number
            before_line: Insert before this line number
            
        Returns:
            True if successful
        """
        if element_name not in self.nodes:
            return False
            
        node = self.nodes[element_name]
        if not hasattr(node, 'body') or not isinstance(node.body, list):
            return False
            
        try:
            new_ast = ast.parse(new_code)
            new_statements = new_ast.body
        except SyntaxError:
            return False
            
        if not new_statements:
            return False
            
        if position == 'start':
            node.body[0:0] = new_statements
        elif position == 'end':
            node.body.extend(new_statements)
        elif after_line:
            result = self._find_statement_in_body(node.body, after_line)
            if result:
                idx, _ = result
                node.body[idx+1:idx+1] = new_statements
            else:
                return False
        elif before_line:
            result = self._find_statement_in_body(node.body, before_line)
            if result:
                idx, _ = result
                node.body[idx:idx] = new_statements
            else:
                return False
        else:
            return False
            
        return True

    def get_element_body_snippet(self, element_name: str, line_start: int, line_end: int) -> Optional[str]:
        """
        Get a specific snippet from within an element's body by line numbers.
        """
        if not self.atok:
            return None
            
        node = self.nodes.get(element_name)
        if not node or not hasattr(node, 'body'):
            return None
            
        # Find statements in the range
        statements = []
        for stmt in node.body:
            if hasattr(stmt, 'lineno') and hasattr(stmt, 'end_lineno'):
                if line_start <= stmt.lineno <= line_end or line_start <= stmt.end_lineno <= line_end:
                    statements.append(stmt)
                    
        if not statements:
            return None
            
        # Generate source for the statements
        return '\n'.join(astor.to_source(stmt).strip() for stmt in statements)

    def _add_imports(self, new_import_nodes: List[Union[ast.Import, ast.ImportFrom]]) -> None:
        """Intelligently adds new import nodes to the top of the AST."""
        existing_imports_str = set()
        last_import_index = -1
        for i, node in enumerate(self.tree.body):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                existing_imports_str.add(astor.to_source(node).strip())
                last_import_index = i
        for new_import in reversed(new_import_nodes):
            new_import_str = astor.to_source(new_import).strip()
            if new_import_str not in existing_imports_str:
                self.tree.body.insert(last_import_index + 1, new_import)

    def replace_element(self, element_name: str, new_code: str) -> bool:
        """
        Replaces a target element with a new block of code.

        This method is more robust than a simple node-for-node replacement.
        It parses the `new_code`, separates imports (which are moved to the top
        of the file) from the main code body (functions, classes, variables, etc.),
        and then replaces the single original element node in the AST with the
        entire new code body. This allows the AI to return code blocks that
        include helper constants or other statements along with the primary
        function or class definition.

        Args:
            element_name: The name of the function or class to replace.
            new_code: A string containing the new Python code.

        Returns:
            True if the replacement was successful, False otherwise.
        """
        if element_name not in self.nodes:
            return False
        try:
            new_ast_module = ast.parse(new_code)
        except SyntaxError:
            return False
        new_imports = [n for n in new_ast_module.body if isinstance(n, (ast.Import, ast.ImportFrom))]
        new_code_body = [n for n in new_ast_module.body if not isinstance(n, (ast.Import, ast.ImportFrom))]
        if not new_code_body:
            return False
        if new_imports:
            self._add_imports(new_imports)
        for node in ast.walk(self.tree):
            if hasattr(node, 'body') and isinstance(node.body, list):
                try:
                    old_node = self.nodes[element_name]
                    idx = node.body.index(old_node)
                    node.body.pop(idx)
                    for i, new_node in enumerate(new_code_body):
                        node.body.insert(idx + i, new_node)
                    del self.nodes[element_name]
                    for n in new_code_body:
                        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                            self.nodes[n.name] = n
                    return True
                except (ValueError, KeyError):
                    continue
        return False

    def add_element(self, new_code: str, anchor_name: Optional[str] = None,
                   before: bool = False) -> bool:
        """
        Adds a new block of code (function, class, variables) to the file.

        This method intelligently handles code snippets from the AI. It separates
        any import statements and adds them to the top of the file. The rest of
        the code block is inserted at an appropriate location, determined either
        by an `anchor_name` or by placing it before the main execution block
        (`if __name__ == '__main__'`).

        Args:
            new_code: The string containing the new function/class/variables.
            anchor_name: The name of an existing element to insert relative to.
            before: If True, insert before the anchor; otherwise, after.

        Returns:
            True if the element block was added successfully, False otherwise.
        """
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
        insertion_index = -1
        main_block_idx = -1
        for i, node in enumerate(self.tree.body):
            if isinstance(node, ast.If) and isinstance(node.test, ast.Compare) and isinstance(node.test.left, ast.Name) and node.test.left.id == '__name__' and len(node.test.ops) == 1 and isinstance(node.test.ops[0], ast.Eq) and len(node.test.comparators) == 1:
                comp = node.test.comparators[0]
                if isinstance(comp, ast.Constant) and comp.value == '__main__' or isinstance(comp, ast.Str) and comp.s == '__main__':
                    main_block_idx = i
                    break
        if anchor_name:
            if anchor_name not in self.nodes:
                return False
            anchor_node = self.nodes[anchor_name]
            try:
                anchor_idx = self.tree.body.index(anchor_node)
                proposed_index = anchor_idx if before else anchor_idx + 1
                if main_block_idx != -1:
                    insertion_index = min(proposed_index, main_block_idx)
                else:
                    insertion_index = proposed_index
            except ValueError:
                return False
        elif main_block_idx != -1:
            insertion_index = main_block_idx
        if insertion_index == -1:
            self.tree.body.extend(new_code_body)
        else:
            for i, new_node in enumerate(new_code_body):
                self.tree.body.insert(insertion_index + i, new_node)
        for node in new_code_body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                self.nodes[node.name] = node
        return True

    def delete_element(self, element_name: str) -> bool:
        """
        Deletes a function, class, variable (ast.Assign), or import (ast.Import/ast.ImportFrom) by its name from the AST.
        Handles top-level elements primarily, with walking for functions and classes.

        Args:
            element_name: The name of the element to delete (function, class, variable, or imported name).

        Returns:
            True if the element was successfully deleted, False otherwise.
        """
        deleted = False
        if element_name in self.nodes:
            node_to_delete = self.nodes[element_name]
            for node in ast.walk(self.tree):
                if hasattr(node, 'body') and isinstance(node.body, list):
                    try:
                        node.body.remove(node_to_delete)
                        deleted = True
                        break
                    except ValueError:
                        continue
            if deleted:
                del self.nodes[element_name]
                self.nodes = self._map_nodes()
                return True
        new_body = []
        for node in self.tree.body:
            if isinstance(node, ast.Assign):
                match = False
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == element_name:
                        match = True
                        break
                if match:
                    deleted = True
                    continue
            elif isinstance(node, ast.Import):
                new_aliases = []
                for alias in node.names:
                    if (alias.name == element_name or alias.asname == element_name):
                        deleted = True
                    else:
                        new_aliases.append(alias)
                if new_aliases:
                    node.names = new_aliases
                elif deleted:
                    continue
            elif isinstance(node, ast.ImportFrom):
                new_aliases = []
                for alias in node.names:
                    if (alias.name == element_name or alias.asname == element_name):
                        deleted = True
                    else:
                        new_aliases.append(alias)
                if new_aliases:
                    node.names = new_aliases
                elif deleted:
                    continue
            new_body.append(node)
        self.tree.body = new_body
        if deleted:
            self.nodes = self._map_nodes()
        return deleted

    def apply_arbitrary_change(self, new_source_code: str) -> bool:
        """
        Rewrites the entire file's AST from a new source string.

        This method parses the provided new_source_code into a new AST.
        If the code is syntactically valid, it replaces the class's internal
        AST (`self.tree`), remaps the file's nodes, and returns True. If
        parsing fails, it returns False.
        """
        try:
            new_tree = ast.parse(new_source_code)
            self.tree = new_tree
            self.nodes = self._map_nodes()
            # Recreate asttokens if available
            if ASTTOKENS_AVAILABLE:
                self.source_code = new_source_code
                self.atok = asttokens.ASTTokens(self.source_code, parse=True)
            return True
        except SyntaxError:
            return False

    def get_modified_source(self) -> str:
        return astor.to_source(self.tree)

    def get_diff(self) -> str:
        modified_source = self.get_modified_source()
        return ''.join(difflib.unified_diff(
            self.source_code.splitlines(keepends=True), 
            modified_source.splitlines(keepends=True),
            fromfile=f'{self.file_path} (original)', 
            tofile=f'{self.file_path} (modified)'
        ))

    def save_changes(self) -> None:
        modified_source = self.get_modified_source()
        with open(self.file_path, 'w') as f:
            f.write(modified_source)