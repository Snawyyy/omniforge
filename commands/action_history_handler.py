from memory_manager import action_memory
from core.action_tracker import action_memory
import os


def handle_action_history_command():
    """Handler for the `action-history` command."""
    actions = action_memory.get_actions()
    if not actions:
        print('[INFO] No actions found in memory.')
        return
    print('[INFO] Refactor Action History:')
    for i, action in enumerate(actions):
        status = action['status'].upper()
        description = action['step'].get('description', 'Unknown action')
        timestamp = action.get('timestamp', 'Unknown time')
        print(f'  {i + 1}. [{status}] {description} ({timestamp})')
        if action['status'] == 'failed':
            print(f"      Error: {action['error']}")
    history_file = os.path.join(os.path.expanduser('~'), '.omniforge',
        'action_history.log')
    if os.path.exists(history_file):
        with open(history_file, 'r') as f:
            lines = f.readlines()
            if len(lines) < len(actions):
                print(
                    f'[WARN] Action history file may be missing entries. Expected at least {len(actions)} lines, found {len(lines)}.'
                    )
    else:
        print('[ERROR] Action history log file does not exist.')
