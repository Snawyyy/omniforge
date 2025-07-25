from core.refactor import Refactor
from utils.logger import log_refactor_complete
from utils.io_helpers import confirm_plan_execution
from core.diff_engine import preview_changes
from core.executor import execute_all_steps, simulate_proposed_changes

def handle_refactor_command(goal: str):
    """
    Main handler for the `refactor` command. Orchestrates the end-to-end
    process of planning, validating, previewing, and applying a multi-file
    transformation based on a high-level user goal.

    Args:
        goal: A natural language description of the desired refactor.
    """
    print(f'[INFO] Initiating refactor with goal: {goal}')
    
    try:
        refactor = Refactor(goal)
        refactor.generate_plan()
        plan = refactor.get_plan()
    except Exception as e:
        print(f'[ERROR] {e}')
        return

    if not plan:
        print('[ERROR] Could not generate a valid refactor plan.')
        return

    try:
        diff_text = simulate_proposed_changes(plan)
    except Exception as e:
        print(f'[ERROR] Failed to simulate changes: {e}')
        return

    preview_changes(diff_text)

    if not confirm_plan_execution(diff_text):
        print('[INFO] Refactor canceled by user.')
        return

    try:
        success = execute_all_steps(plan)
        log_refactor_complete(success, goal)
        status = 'completed' if success else 'partially completed'
        print(f'[OK] Refactor {status} successfully.')
    except Exception as e:
        print(f'[ERROR] Failed during refactor execution: {e}')
        log_refactor_complete(False, goal)

