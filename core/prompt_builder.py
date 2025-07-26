from typing import Dict, Any
import json
from utils.logger import log_prompt_build
from typing import Dict, Any, List
"""
Prompt Builder - A utility for constructing structured prompts for LLM interactions.

This module provides functions to build context-aware prompts for various operations
like editing code or planning refactors, ensuring clarity and precision in model inputs.
"""


def build_refactor_goal_prompt(goal: str, context_summary: Dict[str, Any]
    ) ->str:
    """
    Builds a structured prompt for the refactor command with project context.

    This function generates a detailed prompt that includes the user's high-level goal
    along with relevant project information such as file structure and key snippets,
    guiding the model to produce a precise transformation plan.

    Args:
        goal: The high-level refactoring objective provided by the user.
        context_summary: A dictionary containing summarized project metadata
                         including file paths, languages, and other relevant data.

    Returns:
        A formatted string representing the complete prompt to send to the model.
    """
    formatted_context = _format_context_summary(context_summary)
    prompt = f"""You are an expert software architect tasked with planning a codebase refactor.
Given the following goal and project context, generate a structured transformation plan.

GOAL:
{goal}

PROJECT CONTEXT:
{formatted_context}

OUTPUT FORMAT (JSON SCHEMA):
{{
  "steps": [
    {{
      "type": "CREATE|MODIFY|DELETE|RENAME",
      "file": "<relative_file_path>",
      "description": "<what this step accomplishes>",
      "details": "<specific changes or content>"
    }}
  ]
}}

CONSTRAINTS:
- Each step must clearly define its type and impact.
- Do not use vague descriptions; be specific about file content or actions.
- All file paths must be relative to the project root.
- If you propose creating a new file, include its full intended content.
- If modifying an existing file, describe the exact changes needed using unified diff format when applicable.
- Be concise but comprehensive in your plan.
- Do not include any explanations or markdown in your response - output only valid JSON.
- Ensure all JSON keys are properly quoted and values are correctly escaped.
- Wrap the final output strictly within JSON format as shown without any additional text.
- Do not add any text before or after the JSON object.
- Your response must be parseable as JSON directly.
- Do not make assumptions about unspecified files or behaviors.
- Limit your response to a maximum of 10 steps.
- Do not suggest changes to files not mentioned in the PROJECT CONTEXT unless explicitly required by the GOAL.
- For MODIFY operations, use unified diff format in the 'details' field to show exact line changes.
- For CREATE operations, include the complete file content in the 'details' field.
- For DELETE operations, the 'details' field should explain why the file is being removed.
- For RENAME operations, specify the new file path in the 'details' field.
- All file operations should maintain the project's existing structure and naming conventions.
- Do not propose changes that would break existing functionality unless explicitly instructed.
- Only suggest modifications that directly contribute to achieving the stated GOAL.
- Do not add features, comments, or code not explicitly requested in the GOAL.
- Do not remove or modify existing functionality unless it is directly related to the GOAL.
- Avoid hallucinations by only referencing files and code patterns present in the PROJECT CONTEXT.
- If unsure about a change, prefer omitting it rather than making speculative modifications."""
    return prompt


"""
Prompt Builder - A utility for constructing structured prompts for LLM interactions.

This module provides functions to build context-aware prompts for various operations
like editing code or planning refactors, ensuring clarity and precision in model inputs.
"""


def build_file_view_prompt(files_requested: List[str], context_summary:
    Dict[str, Any]) ->str:
    """
    Builds a structured prompt for file viewing requests with project context.

    This function generates a detailed prompt that includes the list of files the user
    wants to view along with relevant project information such as file structure,
    guiding the model to provide contextual information about those files.

    Args:
        files_requested: A list of file paths that the user wants to view.
        context_summary: A dictionary containing summarized project metadata
                         including file paths, languages, and other relevant data.

    Returns:
        A formatted string representing the complete prompt to send to the model.
    """
    formatted_context = _format_context_summary(context_summary)
    files_list = '\n'.join([f'- {file_path}' for file_path in files_requested])
    prompt = f"""You are an expert software analyst tasked with providing information about specific files in a codebase.

Given the following list of requested files and project context, provide detailed information about each file, including its purpose, contents structure, and role in the project.

REQUESTED FILES:
{files_list}

PROJECT CONTEXT:
{formatted_context}

OUTPUT FORMAT (JSON SCHEMA):
{{
  "files": [
    {{
      "path": "<file_path>",
      "exists": true|false,
      "language": "<programming_language>",
      "size_bytes": <size_of_file>,
      "summary": "<brief_description_of_file_contents>",
      "exported_symbols": ["<function_name>", "<class_name>", "..."],
      "dependencies": ["<dependency_file_path>", "..."]
    }}
  ]
}}

RULES:
- For each file in the request list, provide detailed information as specified in the schema.
- If a file doesn't exist, set "exists" to false and provide explanations in "summary".
- Do not include any explanations or markdown in your response - output only valid JSON.
- Ensure all JSON keys are properly quoted and values are correctly escaped.
- Wrap the final output strictly within JSON format as shown without any additional text.
- Do not add any text before or after the JSON object.
- Your response must be parseable as JSON directly.
- Be concise but comprehensive in your analysis.
- Only provide information about the requested files, not other files in the project.
- Do not make assumptions about file contents not present in the PROJECT CONTEXT."""
    log_prompt_build('file_view', str(files_requested))
    return prompt


"""
Prompt Builder - A utility for constructing structured prompts for LLM interactions.

This module provides functions to build context-aware prompts for various operations
like editing code or planning refactors, ensuring clarity and precision in model inputs.
"""


def _format_context_summary(context_summary: Dict[str, Any]) ->str:
    """Format the project context summary into a readable string for the prompt."""
    formatted = []
    if 'file_structure' in context_summary:
        formatted.append('FILE STRUCTURE:')
        formatted.append(json.dumps(context_summary['file_structure'],
            indent=2))
    if 'key_files' in context_summary:
        formatted.append('\nKEY FILES WITH SNIPPETS:')
        for file_path, snippet in context_summary['key_files'].items():
            formatted.append(f'\n--- {file_path} ---')
            formatted.append(snippet)
    if 'project_info' in context_summary:
        formatted.append('\nPROJECT INFO:')
        for key, value in context_summary['project_info'].items():
            formatted.append(f'{key}: {value}')
    return '\n'.join(formatted)


def build_refactor_goal_prompt(goal: str, context_summary: Dict[str, Any]
    ) ->str:
    """
    Builds a structured prompt for the refactor command with project context.

    This function generates a detailed prompt that includes the user's high-level goal
    along with relevant project information such as file structure and key snippets,
    guiding the model to produce a precise transformation plan.

    Args:
        goal: The high-level refactoring objective provided by the user.
        context_summary: A dictionary containing summarized project metadata
                         including file paths, languages, and other relevant data.

    Returns:
        A formatted string representing the complete prompt to send to the model.
    """
    formatted_context = _format_context_summary(context_summary)
    prompt = f"""You are an expert software architect tasked with planning a codebase refactor.
Given the following goal and project context, generate a structured transformation plan.

GOAL:
{goal}

PROJECT CONTEXT:
{formatted_context}

OUTPUT FORMAT (JSON SCHEMA):
{{
  "steps": [
    {{
      "type": "CREATE|MODIFY|DELETE|RENAME",
      "file": "<relative_file_path>",
      "description": "<what this step accomplishes>",
      "details": "<specific changes or content>"
    }}
  ]
}}

RULES:
- Each step must clearly define its type and impact.
- Do not use vague descriptions; be specific about file content or actions.
- All file paths must be relative to the project root.
- If you propose creating a new file, include its full intended content.
- If modifying an existing file, describe the exact changes needed using unified diff format when applicable.
- Be concise but comprehensive in your plan.
- Do not include any explanations or markdown in your response - output only valid JSON.
- Ensure all JSON keys are properly quoted and values are correctly escaped.
- Wrap the final output strictly within JSON format as shown without any additional text.
- Do not add any text before or after the JSON object.
- Your response must be parseable as JSON directly."""
    log_prompt_build('refactor', goal)
    return prompt


def build_file_view_prompt(requested_files: List[str], context_summary:
    Dict[str, Any]) ->str:
    """
    Builds a structured prompt for viewing files from the project manifest.

    This function generates a detailed prompt that includes a list of requested files
    along with relevant project context, guiding the model to provide comprehensive 
    information about those files.

    Args:
        requested_files: A list of file paths that the user wants to view.
        context_summary: A dictionary containing summarized project metadata
                         including file paths, languages, and other relevant data.

    Returns:
        A formatted string representing the complete prompt to send to the model.
    """
    formatted_context = _format_context_summary(context_summary)
    files_list = '\n'.join(f'- {file_path}' for file_path in requested_files)
    prompt = f"""You are an expert software analyst tasked with providing detailed file information.
Given the following list of requested files and project context, provide comprehensive information 
about each file to help the user understand their content and purpose.

REQUESTED FILES:
{files_list}

PROJECT CONTEXT:
{formatted_context}

OUTPUT FORMAT (JSON SCHEMA):
{{
  "files": [
    {{
      "path": "<file_path>",
      "language": "<programming_language>",
      "size": "<file_size_in_bytes>",
      "summary": "<brief_description_of_file_purpose>",
      "exports": ["<list_of_public_functions_classes_or_variables>"],
      "dependencies": ["<list_of_imported_modules_or_libraries>"]
    }}
  ]
}}

RULES:
- Provide information only for the requested files.
- Do not include any explanations or markdown in your response - output only valid JSON.
- Ensure all JSON keys are properly quoted and values are correctly escaped.
- Wrap the final output strictly within JSON format as shown without any additional text.
- Do not add any text before or after the JSON object.
- Your response must be parseable as JSON directly.
- For 'exports', list only the main public functions, classes, or variables.
- For 'dependencies', list only the imported modules or libraries.
- Be concise but comprehensive in your file summaries.
- Do not make assumptions about file content not present in the project context.
- If a file has no identifiable exports or dependencies, use an empty array for those fields."""
    log_prompt_build('file_view', ', '.join(requested_files))
    return prompt


def _format_context_summary(context_summary: Dict[str, Any]) ->str:
    """
    Formats the project context summary into a readable string representation.

    Args:
        context_summary: Dictionary containing project metadata.

    Returns:
        A formatted string presenting the key aspects of the project context.
    """
    lines = []
    if 'files' in context_summary:
        lines.append('FILES:')
        for f in context_summary['files']:
            lang = f.get('language', 'Unknown')
            size = f.get('size', 0)
            lines.append(f"  - {f['path']} ({lang}, {size} bytes)")
    if 'stats' in context_summary:
        stats = context_summary['stats']
        lines.append('\nSUMMARY STATS:')
        for key, value in stats.items():
            lines.append(f'  {key}: {value}')
    return '\n'.join(lines)


def build_file_view_prompt(file_paths: List[str], context_summary: Dict[str,
    Any]) ->str:
    """
    Builds a structured prompt for viewing specific files from the project.

    This function generates a detailed prompt that includes the requested file paths
    along with relevant project context such as file structure and key snippets,
    guiding the model to provide comprehensive file information.

    Args:
        file_paths: List of relative file paths to be viewed.
        context_summary: A dictionary containing summarized project metadata
                         including file paths, languages, and other relevant data.

    Returns:
        A formatted string representing the complete prompt to send to the model.
    """
    formatted_context = _format_context_summary(context_summary)
    prompt = f"""You are an expert software analyst tasked with providing detailed file information.
Given the following project context and specific file requests, generate comprehensive file descriptions.

REQUESTED FILES:
{json.dumps(file_paths, indent=2)}

PROJECT CONTEXT:
{formatted_context}

OUTPUT FORMAT (JSON SCHEMA):
{{
  "files": [
    {{
      "path": "<relative_file_path>",
      "language": "<programming_language>",
      "size": "<file_size_in_bytes>",
      "content": "<file_content>",
      "description": "<brief_description_of_file_purpose>",
      "exports": ["<list_of_public_functions_classes_or_variables>"]
    }}
  ]
}}

RULES:
- Provide complete and accurate information for each requested file
- Include the full file content in the 'content' field
- Do not include any explanations or markdown in your response - output only valid JSON
- Ensure all JSON keys are properly quoted and values are correctly escaped
- Wrap the final output strictly within JSON format as shown without any additional text
- Do not add any text before or after the JSON object
- Your response must be parseable as JSON directly
- If a file doesn't exist or is inaccessible, include it in the response with an empty content field and explanatory description
- Do not make assumptions about file contents not provided in the context
- Keep descriptions concise but informative
- List only actual exported functions/classes/variables in the 'exports' field
"""
    log_prompt_build('file_view', ', '.join(file_paths))
    return prompt


def _format_context_summary(context_summary: Dict[str, Any]) ->str:
    """
    Formats the project context summary into a readable string representation.

    Args:
        context_summary: Dictionary containing project metadata.

    Returns:
        A formatted string presenting the key aspects of the project context.
    """
    lines = []
    if 'files' in context_summary:
        lines.append('FILES:')
        for f in context_summary['files']:
            lang = f.get('language', 'Unknown')
            size = f.get('size', 0)
            lines.append(f"  - {f['path']} ({lang}, {size} bytes)")
    if 'stats' in context_summary:
        stats = context_summary['stats']
        lines.append('\nSUMMARY STATS:')
        for key, value in stats.items():
            lines.append(f'  {key}: {value}')
    return '\n'.join(lines)
