from utils.errors import PlanParsingError
from core.model_client import send_prompt_to_model
from typing import Dict, Any, Optional
import logging
import json
import re
from typing import List, Tuple
from core.instruction_enhancer import enhance_instruction
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
