"""
CodeEditor - Enhanced AST-based code manipulation tool

This module provides a class to programmatically parse, analyze,
and edit source code. It has been refactored to use a pluggable
ASTAdapter system, allowing it to support multiple languages.
Currently, it defaults to Python's built-in `ast` module via
PythonASTAdapter for backward compatibility during the transition.
"""
import ast
import astor
import difflib
from typing import List, Optional, Dict, Union, Tuple, Type, Any
from ast_adapter import ASTAdapter
import os
from rich.text import Text
try:
    import asttokens
    ASTTOKENS_AVAILABLE = True
except ImportError:
    ASTTOKENS_AVAILABLE = False


class CodeEditor:
    """
    An enhanced class to safely edit files using AST/CST with partial edit support.
    The core logic for interacting with the code structure is now delegated to
    a language-specific ASTAdapter.
    """

    def __init__(self, file_path: str, adapter_class: Optional[Type[
        ASTAdapter]]=None):
        """
        Initializes the CodeEditor.

        Args:
            file_path: The path to the source file.
            adapter_class: The ASTAdapter subclass to use. If None, defaults to
                           PythonASTAdapter for .py files.
        """
        self.file_path = file_path
        self.source_code = self._read_file()
        self.adapter: Optional[ASTAdapter] = None
        self.tree: Optional[ast.AST] = None
        self.nodes: Dict[str, ast.AST] = {}
        self.atok: Optional[Any] = None
        if adapter_class is None:
            file_extension = os.path.splitext(self.file_path)[1].lower()
            if file_extension == '.py':
                try:
                    from python_ast_adapter import PythonASTAdapter
                    self.adapter = PythonASTAdapter(self.source_code)
                except ImportError:
                    try:
                        self.tree = self._parse_source()
                        self.nodes = self._map_nodes()
                        if ASTTOKENS_AVAILABLE:
                            self.atok = asttokens.ASTTokens(self.
                                source_code, parse=True)
                    except Exception as parse_error:
                        raise ValueError(
                            f'Failed to parse Python file: {parse_error}')
            elif file_extension == '.js':
                try:
                    from javascript_ast_adapter import JavaScriptASTAdapter
                    self.adapter = JavaScriptASTAdapter(self.source_code)
                except ImportError as e:
                    raise ValueError(
                        f'tree-sitter is required for JavaScript support but not available: {e}'
                        )
                except Exception as e:
                    raise ValueError(
                        f'Failed to initialize JavaScript adapter: {e}')
            elif file_extension == '.txt':
                pass
            else:
                raise ValueError(
                    f'Unsupported file type: {file_extension}. Supported types: .py, .js, .txt'
                    )
        else:
            try:
                self.adapter = adapter_class(self.source_code)
            except Exception as e:
                raise ValueError(
                    f'Failed to initialize adapter {adapter_class.__name__}: {e}'
                    )

    def _read_file(self) ->str:
        """Reads the source file."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise ValueError(f'File not found: {self.file_path}')

    def _parse_source(self) ->ast.AST:
        """Fallback parsing logic."""
        try:
            return ast.parse(self.source_code)
        except SyntaxError as e:
            raise ValueError(f'Invalid Python syntax in {self.file_path}: {e}')

    def list_elements(self) ->List[str]:
        """Lists top-level elements in the code."""
        if self.adapter:
            return self.adapter.list_elements()
        else:
            return list(self.nodes.keys())

    def get_source_of(self, element_name: str) ->Optional[str]:
        """Gets the source code for a specific element."""
        if self.adapter:
            return self.adapter.get_source_of(element_name)
        else:
            node = self.nodes.get(element_name)
            return astor.to_source(node) if node else None

    def get_element_structure(self, element_name: str) ->Optional[Dict]:
        """Gets detailed structure information about an element."""
        if self.adapter:
            return self.adapter.get_element_structure(element_name)
        else:
            node = self.nodes.get(element_name)
            if not node:
                return None
            structure = {'name': element_name, 'type': node.__class__.
                __name__, 'line_start': node.lineno if hasattr(node,
                'lineno') else None, 'line_end': node.end_lineno if hasattr
                (node, 'end_lineno') else None, 'body_items': []}
            if hasattr(node, 'body'):
                for i, item in enumerate(node.body):
                    item_info = {'index': i, 'type': item.__class__.
                        __name__, 'line_start': item.lineno if hasattr(item,
                        'lineno') else None, 'line_end': item.end_lineno if
                        hasattr(item, 'end_lineno') else None}
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

    def get_element_body_snippet(self, element_name: str, line_start: int,
        line_end: int) ->Optional[str]:
        """Gets a snippet from within an element's body."""
        if self.adapter:
            return self.adapter.get_element_body_snippet(element_name,
                line_start, line_end)
        else:
            if not self.atok:
                return None
            node = self.nodes.get(element_name)
            if not node or not hasattr(node, 'body'):
                return None
            statements = []
            for stmt in node.body:
                if hasattr(stmt, 'lineno') and hasattr(stmt, 'end_lineno'):
                    if (line_start <= stmt.lineno <= line_end or line_start <=
                        stmt.end_lineno <= line_end):
                        statements.append(stmt)
            if not statements:
                return None
            return '\n'.join(astor.to_source(stmt).strip() for stmt in
                statements)

    def replace_partial(self, element_name: str, new_code: str, line_start:
        Optional[int]=None, line_end: Optional[int]=None, statement_index:
        Optional[int]=None) ->bool:
        """Replaces a partial section of an element."""
        if self.adapter:
            return self.adapter.replace_partial(element_name, new_code,
                line_start, line_end, statement_index)
        else:
            if element_name not in self.nodes:
                return False
            node = self.nodes[element_name]
            if not hasattr(node, 'body') or not isinstance(node.body, list):
                return False
            try:
                if new_code.strip().startswith('def ') or new_code.strip(
                    ).startswith('class '):
                    new_ast = ast.parse(new_code)
                    new_statements = new_ast.body[0].body
                else:
                    new_ast = ast.parse(new_code)
                    new_statements = new_ast.body
            except SyntaxError:
                return False
            if not new_statements:
                return False
            if statement_index is not None:
                if 0 <= statement_index < len(node.body):
                    node.body[statement_index:statement_index + 1
                        ] = new_statements
                    return True
            elif line_start is not None:
                result = self._find_statement_in_body(node.body, line_start,
                    line_end)
                if result:
                    idx, _ = result
                    if line_end:
                        end_idx = idx
                        for i in range(idx + 1, len(node.body)):
                            stmt = node.body[i]
                            if hasattr(stmt, 'end_lineno'
                                ) and stmt.end_lineno <= line_end:
                                end_idx = i
                            else:
                                break
                        node.body[idx:end_idx + 1] = new_statements
                    else:
                        node.body[idx:idx + 1] = new_statements
                    return True
            return False

    def add_element(self, new_code: str, anchor_name: Optional[str]=None,
        before: bool=False) ->bool:
        """Adds a new block of code to the file."""
        if self.adapter:
            return self.adapter.add_element(new_code, anchor_name, before)
        else:
            try:
                new_ast_module = ast.parse(new_code)
            except (SyntaxError, IndexError):
                return False
            new_imports = [n for n in new_ast_module.body if isinstance(n,
                (ast.Import, ast.ImportFrom))]
            new_code_body = [n for n in new_ast_module.body if not
                isinstance(n, (ast.Import, ast.ImportFrom))]
            if not new_code_body:
                return False
            if new_imports:
                self._add_imports(new_imports)
            insertion_index = -1
            main_block_idx = -1
            for i, _node in enumerate(self.tree.body):
                if isinstance(_node, ast.If) and isinstance(_node.test, ast
                    .Compare) and isinstance(_node.test.left, ast.Name
                    ) and _node.test.left.id == '__name__' and len(_node.
                    test.ops) == 1 and isinstance(_node.test.ops[0], ast.Eq
                    ) and len(_node.test.comparators) == 1:
                    comp = _node.test.comparators[0]
                    if isinstance(comp, ast.Constant
                        ) and comp.value == '__main__' or isinstance(comp,
                        ast.Str) and comp.s == '__main__':
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
            for _node in new_code_body:
                if isinstance(_node, (ast.FunctionDef, ast.AsyncFunctionDef,
                    ast.ClassDef)):
                    self.nodes[_node.name] = _node
            return True

    def delete_element(self, element_name: str) ->bool:
        """Deletes an element by name."""
        if self.adapter:
            return self.adapter.delete_element(element_name)
        else:
            deleted = False
            if element_name in self.nodes:
                node_to_delete = self.nodes[element_name]
                for _node in ast.walk(self.tree):
                    if hasattr(_node, 'body') and isinstance(_node.body, list):
                        try:
                            _node.body.remove(node_to_delete)
                            deleted = True
                            break
                        except ValueError:
                            continue
                if deleted:
                    del self.nodes[element_name]
                    self.nodes = self._map_nodes()
                    return True
            new_body = []
            for _node in self.tree.body:
                if isinstance(_node, ast.Assign):
                    match = False
                    for target in _node.targets:
                        if isinstance(target, ast.Name
                            ) and target.id == element_name:
                            match = True
                            break
                    if match:
                        deleted = True
                        continue
                elif isinstance(_node, ast.Import):
                    new_aliases = []
                    for alias in _node.names:
                        if not (alias.name == element_name or alias.asname ==
                            element_name):
                            new_aliases.append(alias)
                        else:
                            deleted = True
                    if new_aliases:
                        _node.names = new_aliases
                    elif deleted:
                        continue
                elif isinstance(_node, ast.ImportFrom):
                    new_aliases = []
                    for alias in _node.names:
                        if not (alias.name == element_name or alias.asname ==
                            element_name):
                            new_aliases.append(alias)
                        else:
                            deleted = True
                    if new_aliases:
                        _node.names = new_aliases
                    elif deleted:
                        continue
                new_body.append(_node)
            self.tree.body = new_body
            if deleted:
                self.nodes = self._map_nodes()
            return deleted

    def replace_element(self, element_name: str, new_code: str) ->bool:
        """Replaces a target element with new code."""
        if self.adapter:
            return self.adapter.replace_element(element_name, new_code)
        else:
            if element_name not in self.nodes:
                return False
            try:
                new_ast_module = ast.parse(new_code)
            except SyntaxError:
                return False
            new_imports = [n for n in new_ast_module.body if isinstance(n,
                (ast.Import, ast.ImportFrom))]
            new_code_body = [n for n in new_ast_module.body if not
                isinstance(n, (ast.Import, ast.ImportFrom))]
            if not new_code_body:
                return False
            if new_imports:
                self._add_imports(new_imports)
            for _node in ast.walk(self.tree):
                if hasattr(_node, 'body') and isinstance(_node.body, list):
                    try:
                        old_node = self.nodes[element_name]
                        idx = _node.body.index(old_node)
                        _node.body.pop(idx)
                        for i, new_node in enumerate(new_code_body):
                            _node.body.insert(idx + i, new_node)
                        del self.nodes[element_name]
                        for n in new_code_body:
                            if isinstance(n, (ast.FunctionDef, ast.
                                AsyncFunctionDef, ast.ClassDef)):
                                self.nodes[n.name] = n
                        return True
                    except (ValueError, KeyError):
                        continue
            return False

    def insert_in_element(self, element_name: str, new_code: str, position:
        str='end', after_line: Optional[int]=None, before_line: Optional[
        int]=None) ->bool:
        """
        Insert new code into an element without replacing existing code.
        This is an internal/helper method, delegating to adapter OR using fallback.
        """
        if self.adapter:
            return self.adapter.add_element(new_code, anchor_name=
                element_name, before=position == 'start')
        else:
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
                    node.body[idx + 1:idx + 1] = new_statements
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

    def _map_nodes(self) ->Dict[str, ast.AST]:
        """Fallback node mapping logic for Python AST."""
        nodes = {}
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast
                .ClassDef)):
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

    def _find_statement_in_body(self, body: List[ast.AST], line_start: int,
        line_end: Optional[int]=None) ->Optional[Tuple[int, ast.AST]]:
        """Fallback statement finding logic for Python AST."""
        for i, stmt in enumerate(body):
            if hasattr(stmt, 'lineno'):
                if line_end:
                    stmt_end = stmt.end_lineno if hasattr(stmt, 'end_lineno'
                        ) else stmt.lineno
                    if (stmt.lineno <= line_start <= stmt_end or stmt.
                        lineno <= line_end <= stmt_end):
                        return i, stmt
                elif stmt.lineno == line_start:
                    return i, stmt
        return None

    def _add_imports(self, new_import_nodes: List[Union[ast.Import, ast.
        ImportFrom]]) ->None:
        """Fallback logic to add imports to the top of the Python AST."""
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

    def apply_arbitrary_change(self, new_source_code: str) ->bool:
        """
        Rewrites the entire file's AST from a new source string.
        This method resets the adapter if one exists, or uses fallback.
        """
        if self.adapter:
            try:
                adapter_class = type(self.adapter)
                self.adapter = adapter_class(new_source_code)
                return True
            except Exception:
                return False
        else:
            try:
                new_tree = ast.parse(new_source_code)
                self.tree = new_tree
                self.nodes = self._map_nodes()
                if ASTTOKENS_AVAILABLE:
                    self.source_code = new_source_code
                    self.atok = asttokens.ASTTokens(self.source_code, parse
                        =True)
                return True
            except SyntaxError:
                return False

    def get_modified_source(self) ->str:
        """Serializes the potentially modified code structure back to source."""
        if self.adapter:
            return self.adapter.get_modified_source()
        else:
            return astor.to_source(self.tree)

    def get_diff(self) ->str:
        """Generates a diff between the original source and the modified source."""
        if self.adapter:
            return self.adapter.get_diff()
        else:
            modified_source = self.get_modified_source()
            diff_lines = difflib.unified_diff(self.source_code.splitlines(keepends=True),
                                              modified_source.splitlines(keepends=True),
                                              fromfile=f'{self.file_path} (original)',
                                              tofile=f'{self.file_path} (modified)')
            colored_diff_lines = []
            for line in diff_lines:
                if line.startswith('+'):
                    colored_diff_lines.append(str(Text(line, style="green")))
                elif line.startswith('-'):
                    colored_diff_lines.append(str(Text(line, style="red")))
                else:
                    colored_diff_lines.append(line)
            return ''.join(colored_diff_lines)

    def save_changes(self) ->None:
        """Saves the modified source code back to the file."""
        modified_source = self.get_modified_source()
        with open(self.file_path, 'w', encoding='utf-8') as f:
            f.write(modified_source)
