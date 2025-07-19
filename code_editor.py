#!/usr/bin/env python3

"""
CodeEditor - AST-based Python code manipulation tool

This module provides a class to programmatically parse, analyze,
and edit Python source code using Abstract Syntax Trees (AST).
It allows for targeted replacement and addition of functions and classes,
and intelligently handles new import statements.
"""

import ast
import astor
import difflib
from typing import List, Optional, Dict, Union

class CodeEditor:
    """A class to safely edit Python files using AST."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.source_code = self._read_file()
        self.tree: ast.AST = self._parse_source()
        self.nodes: Dict[str, ast.AST] = self._map_nodes()

    def _read_file(self) -> str:
        try:
            with open(self.file_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            raise ValueError(f"File not found: {self.file_path}")

    def _parse_source(self) -> ast.AST:
        try:
            return ast.parse(self.source_code)
        except SyntaxError as e:
            raise ValueError(f"Invalid Python syntax in {self.file_path}: {e}")

    def _map_nodes(self) -> Dict[str, ast.AST]:
        nodes = {}
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name not in nodes:
                    nodes[node.name] = node
        return nodes

    def list_elements(self) -> List[str]:
        return list(self.nodes.keys())

    def get_source_of(self, element_name: str) -> Optional[str]:
        node = self.nodes.get(element_name)
        return astor.to_source(node) if node else None

    def _add_imports(self, new_import_nodes: List[Union[ast.Import, ast.ImportFrom]]) -> None:
        """Intelligently adds new import nodes to the top of the AST."""
        existing_imports_str = set()
        last_import_index = -1

        # First, find all existing imports and the position of the last one
        for i, node in enumerate(self.tree.body):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                existing_imports_str.add(astor.to_source(node).strip())
                last_import_index = i

        # Insert new imports that don't already exist, starting after the last import
        for new_import in reversed(new_import_nodes):
            new_import_str = astor.to_source(new_import).strip()
            if new_import_str not in existing_imports_str:
                self.tree.body.insert(last_import_index + 1, new_import)

    def replace_element(self, element_name: str, new_code: str) -> bool:
        if element_name not in self.nodes:
            return False

        try:
            new_ast_module = ast.parse(new_code)
            
            new_imports = [n for n in new_ast_module.body if isinstance(n, (ast.Import, ast.ImportFrom))]
            new_definitions = [n for n in new_ast_module.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]

            if len(new_definitions) != 1:
                return False
            
            new_node = new_definitions[0]

        except (SyntaxError, IndexError):
            return False

        if new_imports:
            self._add_imports(new_imports)

        for node in ast.walk(self.tree):
            if hasattr(node, 'body') and isinstance(node.body, list):
                for i, child in enumerate(node.body):
                    if child == self.nodes[element_name]:
                        node.body[i] = new_node
                        self.nodes[new_node.name] = new_node # Update map in case of rename
                        return True
        return False

    def get_modified_source(self) -> str:
        return astor.to_source(self.tree)

    def get_diff(self) -> str:
        modified_source = self.get_modified_source()
        return "".join(difflib.unified_diff(
            self.source_code.splitlines(keepends=True),
            modified_source.splitlines(keepends=True),
            fromfile=f"{self.file_path} (original)",
            tofile=f"{self.file_path} (modified)",
        ))

    def save_changes(self) -> None:
        modified_source = self.get_modified_source()
        with open(self.file_path, 'w') as f:
            f.write(modified_source)