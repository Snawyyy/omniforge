from context.context_manager import get_project_context_summary
from utils.logger import log_refactor_complete
from utils.io_helpers import confirm_plan_execution
from core.prompt_builder import build_refactor_goal_prompt
from core.diff_engine import preview_changes
from core.executor import execute_all_steps, simulate_proposed_changes


def validate_steps(steps: List[Dict[str, Any]]) ->List[Dict[str, Any]]:
    """
    Enhanced validation of refactor steps with stricter checks.
    
    Args:
        steps: List of step dictionaries from the AI-generated plan
        
    Returns:
        List of validated steps
        
    Raises:
        ValueError: If steps fail validation
    """
    if not isinstance(steps, list):
        raise ValueError('Steps must be a list')
    if not steps:
        raise ValueError('Steps cannot be empty')
    required_fields = {'type', 'file', 'description'}
    modification_types = {'edit', 'add', 'delete', 'refactor'}
    validated_steps = []
    for i, step in enumerate(steps):
        if not isinstance(step, dict):
            raise ValueError(f'Step {i} must be a dictionary')
        missing_fields = required_fields - set(step.keys())
        if missing_fields:
            raise ValueError(
                f'Step {i} missing required fields: {missing_fields}')
        if step['type'] not in modification_types:
            raise ValueError(
                f"Step {i} has invalid type '{step['type']}'. Must be one of {modification_types}"
                )
        if not isinstance(step['file'], str) or not step['file'].strip():
            raise ValueError(f'Step {i} has invalid file path')
        if not isinstance(step['description'], str) or not step['description'
            ].strip():
            raise ValueError(f'Step {i} has invalid description')
        if step['type'] == 'edit':
            if 'search' not in step and 'line_number' not in step:
                raise ValueError(
                    f"Edit step {i} must include either 'search' or 'line_number'"
                    )
        if step['type'] == 'add':
            if 'content' not in step:
                raise ValueError(f"Add step {i} must include 'content'")
        validated_steps.append(step)
    return validated_steps


import json
from typing import List, Dict, Any


def handle_refactor_command(goal: str):
    """
    Main handler for the `refactor` command. Orchestrates the end-to-end
    process of planning, validating, previewing, and applying a multi-file
    transformation based on a high-level user goal.

    Args:
        goal: A natural language description of the desired refactor.
    """
    print(f'[INFO] Initiating refactor with goal: {goal}')
    context_summary = get_project_context_summary()
    refactor_prompt = build_refactor_goal_prompt(goal, context_summary)
    try:
        plan_json = request_structured_plan(refactor_prompt)
    except Exception as e:
        print(f'[ERROR] Failed to generate refactor plan: {e}')
        return
    try:
        validated_plan = validate_steps(plan_json.get('steps', []))
    except ValueError as e:
        print(f'[ERROR] Invalid plan received: {e}')
        return
    try:
        diff_text = simulate_proposed_changes(validated_plan)
    except Exception as e:
        print(f'[ERROR] Failed to simulate changes: {e}')
        return
    preview_changes(diff_text)
    if not confirm_plan_execution(diff_text):
        print('[INFO] Refactor canceled by user.')
        return
    try:
        success = execute_all_steps(validated_plan)
        log_refactor_complete(success, goal)
        status = 'completed' if success else 'partially completed'
        print(f'[OK] Refactor {status} successfully.')
    except Exception as e:
        print(f'[ERROR] Failed during refactor execution: {e}')
        log_refactor_complete(False, goal)
