from typing import Dict, Any
import json
from utils.logger import log_prompt_build
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
