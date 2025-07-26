from core.refactor import Refactor
from utils.logger import log_refactor_complete
from utils.io_helpers import confirm_plan_execution
from core.diff_engine import preview_changes
from core.executor import execute_all_steps, simulate_proposed_changes
import os
from core.dynamic_context import extract_referenced_files, dynamic_look_at_file
from core.planner import request_structured_plan, validate_steps
from core.prompt_builder import build_refactor_goal_prompt
from context.context_manager import get_project_context_summary
from core.action_tracker import ActionTracker
from core.executor import execute_all_steps
from core.diff_engine import preview_changes, simulate_proposed_changes
from core.dynamic_context import dynamic_look_at_file
from utils.io_helpers import extract_referenced_files


def handle_refactor_command(goal: str):
    """
    Main handler for the `refactor` command. Orchestrates the end-to-end
    process of planning, validating, previewing, and applying a multi-file
    transformation based on a high-level user goal.

    Args:
        goal: A natural language description of the desired refactor.
    """
    print(f'[INFO] Initiating refactor with goal: {goal}')
    action_tracker = ActionTracker()
    action_tracker.start_refactor(goal)
    try:
        refactor = Refactor(goal)
        refactor.generate_plan()
        plan = refactor.get_plan()
        if plan and 'steps' in plan:
            for step in plan['steps']:
                action_tracker.action_memory.add_action(step, 'planned')
    except Exception as e:
        action_tracker.record_error('plan_generation', str(e))
        print(f'[ERROR] {e}')
        return
    if not plan:
        action_tracker.record_error('plan_validation',
            'Could not generate a valid refactor plan.')
        print('[ERROR] Could not generate a valid refactor plan.')
        return
    try:
        diff_text = simulate_proposed_changes(plan.get('steps', []))
        action_tracker.record_simulation(diff_text)
    except Exception as e:
        action_tracker.record_error('simulation', str(e))
        print(f'[ERROR] Failed to simulate changes: {e}')
        return
    preview_changes(diff_text)
    if not confirm_plan_execution(diff_text):
        action_tracker.record_cancellation()
        print('[INFO] Refactor canceled by user.')
        return
    action_tracker.record_execution_start(plan.get('steps', []))
    try:
        success = execute_all_steps(plan.get('steps', []), action_tracker)
        action_tracker.record_completion(success)
        log_refactor_complete(success, goal)
        status = 'completed' if success else 'partially completed'
        print(f'[OK] Refactor {status} successfully.')
    except Exception as e:
        action_tracker.record_error('execution', str(e))
        print(f'[ERROR] Failed during refactor execution: {e}')
        log_refactor_complete(False, goal)
