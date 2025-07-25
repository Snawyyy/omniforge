from context.context_manager import get_project_context_summary
from utils.logger import log_refactor_complete
from utils.io_helpers import confirm_plan_execution
from core.prompt_builder import build_refactor_goal_prompt
from core.diff_engine import preview_changes
from core.executor import execute_all_steps, simulate_proposed_changes
from core.planner import request_structured_plan, validate_steps


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
