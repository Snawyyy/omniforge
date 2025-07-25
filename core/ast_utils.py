from typing import Optional
import os
import ast
import keyword
from typing import List, Optional, Union
from core.python_ast_adapter import PythonASTAdapter
from typing import Optional, List, Any
import astor


def parse_ast_from_file(file_path: str) ->Optional[ast.AST]:
    """
    Parses a Python source file into an AST object with proper error handling.

    Args:
        file_path: The path to the Python source file.

    Returns:
        The parsed AST object if successful, None otherwise.

    Raises:
        ValueError: If the file is not found or has invalid Python syntax.
    """
    if not os.path.exists(file_path):
        raise ValueError(f'File not found: {file_path}')
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        return ast.parse(source_code)
    except SyntaxError as e:
        raise ValueError(f'Invalid Python syntax in {file_path}: {e}')
    except Exception as e:
        raise ValueError(f'Error reading or parsing {file_path}: {e}')


"""
AST Utilities - Helper functions for AST parsing and node manipulation.
"""


def find_target_nodes(tree: ast.AST, instruction: str) ->List[ast.AST]:
    """
    Locates specific nodes in an AST based on name or instruction.
    
    This function walks the AST and attempts to find nodes that match
    the given instruction. It can handle various types of instructions:
    - Function names: "edit function my_function"
    - Class names: "modify class MyClass"
    - Variable names: "change variable my_var"
    - General instructions: "add error handling to the main function"
    
    Args:
        tree: The AST tree to search in.
        instruction: A string instruction describing what to find.
        
    Returns:
        A list of AST nodes that match the instruction.
    """
    tokens = instruction.lower().split()
    target_names = []
    for i, token in enumerate(tokens):
        if token in ('function', 'class', 'variable', 'modify', 'edit',
            'change') and i + 1 < len(tokens):
            potential_name = tokens[i + 1]
            if potential_name.isidentifier() and not keyword.iskeyword(
                potential_name):
                target_names.append(potential_name)
    if not target_names:
        for token in tokens:
            if token.isidentifier() and not keyword.iskeyword(token):
                target_names.append(token)
    if not target_names:
        target_names = ['main', '__main__', 'run', 'execute']
    matching_nodes = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in target_names:
                matching_nodes.append(node)
        elif isinstance(node, ast.ClassDef):
            if node.name in target_names:
                matching_nodes.append(node)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in target_names:
                    matching_nodes.append(node)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name
                    if name in target_names:
                        matching_nodes.append(node)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname or alias.name
                    if name in target_names:
                        matching_nodes.append(node)
    if not matching_nodes:
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast
                .ClassDef)):
                matching_nodes.append(node)
    return matching_nodes


def apply_model_patch(source_code: str, target_element_name: str,
    model_response: str) ->Optional[str]:
    """
    Applies a model-generated patch to a specific element within the source code using AST-based transformation.

    Args:
        source_code: The original source code as a string.
        target_element_name: The name of the function/class/element to modify.
        model_response: The LLM-generated code snippet or replacement.

    Returns:
        The modified source code as a string, or None if the operation fails.
    """
    try:
        adapter = PythonASTAdapter(source_code)
        if adapter.replace_element(target_element_name, model_response):
            return adapter.get_modified_source()
        try:
            temp_module = ast.parse(model_response.strip())
            if len(temp_module.body) == 1 and hasattr(temp_module.body[0],
                'body'):
                pass
        except SyntaxError:
            pass
        return None
    except Exception:
        return None
