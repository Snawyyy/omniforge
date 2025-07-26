from memory_manager import action_memory


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
