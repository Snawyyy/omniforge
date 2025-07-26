from utils.errors import PlanParsingError
from core.model_client import send_prompt_to_model
from typing import Dict, Any, Optional
import logging
import json
import re
from typing import List, Tuple
from core.instruction_enhancer import enhance_instruction
from utils.logger import log_planning_step
from core.prompt_builder import build_refactor_goal_prompt
from typing import Dict, Any, List
from utils.logger import log_planning_activity
from core.model_client import query_model_safe
from core.prompt_builder import build_file_view_prompt
from utils.logger import log_planning_complete
logger = logging.getLogger(__name__)
logger = logging.getLogger(__name__)


def request_structured_plan(prompt_text: str, expected_keys: Optional[set]=None
    ) ->Dict[str, Any]:
    """
    Requests a structured transformation plan from the LLM and parses the response.

    Args:
        prompt_text (str): Formatted prompt to send to the model.
        expected_keys (Optional[set]): Set of top-level keys expected in the plan (e.g., {"steps", "metadata"}).

    Returns:
        Dict[str, Any]: Parsed plan as a dictionary.

    Raises:
        PlanParsingError: If the model's response is not valid JSON or lacks required keys.
    """
    enhanced_prompt = enhance_instruction(prompt_text)
    logger.debug('Sending structured plan request to model.')
    raw_response = send_prompt_to_model(enhanced_prompt)
    json_match = re.search('\\{.*\\}', raw_response, re.DOTALL)
    if json_match:
        raw_response = json_match.group(0)
    try:
        parsed_plan = json.loads(raw_response)
    except json.JSONDecodeError as e:
        logger.error('Failed to decode JSON from model response.')
        raise PlanParsingError('Model response is not valid JSON.') from e
    if expected_keys:
        missing_keys = expected_keys - set(parsed_plan.keys())
        if missing_keys:
            logger.error(
                f'Model response missing expected keys: {missing_keys}')
            raise PlanParsingError(
                f'Missing required keys in plan: {missing_keys}')
    logger.debug('Structured plan successfully parsed.')
    return parsed_plan


def plan_file_view_action(user_request: str, project_context: Dict[str, Any]
    ) ->Dict[str, Any]:
    """
    Plans a file viewing action based on user request and project context.
    
    Args:
        user_request: Natural language request for files to view
        project_context: Current project metadata and structure
        
    Returns:
        Dict containing the planned file viewing action
    """
    prompt = build_file_view_prompt(user_request, project_context)
    log_planning_activity('file_view', user_request)
    response = query_model_safe(prompt)
    if not response:
        return {'error': 'Failed to generate file view plan'}
    try:
        plan = json.loads(response)
        return {'action': 'view_files', 'files': plan.get('files', []),
            'reasoning': plan.get('reasoning', '')}
    except json.JSONDecodeError:
        return {'error': 'Invalid response format from model'}


def plan_file_view_action(user_request: str, project_context: Dict[str, Any]
    ) ->Dict[str, Any]:
    """
    Plan a file viewing action based on user request and project context.
    
    Args:
        user_request: User's request for files to view
        project_context: Current project context information
        
    Returns:
        A structured plan for file viewing actions
    """
    log_planning_step('file_view', user_request)
    prompt = f"""You are an expert software architect tasked with planning file viewing actions.
Given the following user request and project context, generate a structured plan to view relevant files.

USER REQUEST:
{user_request}

PROJECT CONTEXT:
{project_context}

OUTPUT FORMAT (JSON SCHEMA):
{{
  "steps": [
    {{
      "type": "VIEW",
      "file": "<relative_file_path>",
      "description": "<reason for viewing this file>",
      "details": "<specific content or sections to focus on>"
    }}
  ]
}}

RULES:
- Only include files that are directly relevant to the user's request
- Each step must clearly define which file to view and why
- Be specific about content or sections of interest
- Do not include files not mentioned in the project context
- Limit to maximum 5 most relevant files
- Output only valid JSON as shown in the schema
- Do not add any explanations outside the JSON structure"""
    return {'steps': []}


def validate_steps(steps: List[Dict[str, Any]]) ->Tuple[bool, List[str]]:
    """
    Validates transformation steps for safety and correctness.
    
    Args:
        steps: List of step dictionaries containing 'type', 'target', and 'content' keys
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    if not isinstance(steps, list):
        errors.append('Steps must be a list')
        return False, errors
    valid_types = {'create', 'modify', 'delete', 'rename'}
    file_path_pattern = re.compile('^[a-zA-Z0-9_./-]+\\.[a-zA-Z0-9]+$')
    for i, step in enumerate(steps):
        if not isinstance(step, dict):
            errors.append(f'Step {i} is not a dictionary')
            continue
        if 'type' not in step:
            errors.append(f"Step {i} missing 'type' key")
            continue
        step_type = step['type'].lower()
        if step_type not in valid_types:
            errors.append(
                f"Step {i} has invalid type '{step_type}'. Must be one of: {valid_types}"
                )
            continue
        if step_type in ('create', 'modify', 'rename'
            ) and 'target' not in step:
            errors.append(f"Step {i} ({step_type}) missing 'target' key")
        elif step_type == 'create' and 'content' not in step:
            errors.append(f"Step {i} (create) missing 'content' key")
        elif step_type == 'rename' and 'new_target' not in step:
            errors.append(f"Step {i} (rename) missing 'new_target' key")
        for path_key in ['target', 'new_target']:
            if path_key in step:
                path = step[path_key]
                if not isinstance(path, str):
                    errors.append(f'Step {i} has non-string {path_key}')
                elif not file_path_pattern.match(path):
                    errors.append(
                        f'Step {i} has invalid {path_key} format: {path}')
    return len(errors) == 0, errors


def plan_file_view_action(user_request: str, context_summary: Dict[str, Any]
    ) ->Dict[str, Any]:
    """
    Plans a file viewing action based on user request and project context.
    
    Args:
        user_request: User's natural language request for files to view
        context_summary: Current project context including file structure
        
    Returns:
        A structured plan for which files to present to the user
    """
    formatted_context = _format_file_view_context(context_summary)
    prompt = f"""You are an expert software analyst tasked with identifying the most relevant files to show a developer.

Given the following user request and project context, generate a list of files that would be most helpful to view.

USER REQUEST:
{user_request}

PROJECT CONTEXT:
{formatted_context}

OUTPUT FORMAT (JSON SCHEMA):
{{
  "files_to_show": [
    {{
      "file_path": "<relative_file_path>",
      "reason": "<why this file is relevant>"
    }}
  ]
}}

RULES:
- Include only files that directly relate to the user's request
- Limit your response to at most 5 files
- All file paths must be relative to the project root
- Do not include any markdown or formatting in your response
- Output only valid JSON as shown in the schema
- Ensure all JSON keys are properly quoted
- Do not add any text before or after the JSON object"""
    log_planning_complete('file_view', user_request)
    return {'files_to_show': []}


def _format_file_view_context(context_summary: Dict[str, Any]) ->str:
    """Format context specifically for file viewing decisions."""
    lines = []
    if 'file_structure' in context_summary:
        lines.append('FILE STRUCTURE:')
        lines.append(json.dumps(context_summary['file_structure'], indent=2))
    if 'key_files' in context_summary:
        lines.append('\nKEY FILES WITH SNIPPETS:')
        for file_path, snippet in context_summary['key_files'].items():
            lines.append(f'\n--- {file_path} ---')
            lines.append(snippet)
    return '\n'.join(lines)
