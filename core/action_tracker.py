from utils.logger import log_action_tracker_event
from typing import Dict, List, Optional
from datetime import datetime
import os
import json
import time
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict
from memory_manager import ActionMemoryManager
from typing import List, Dict, Optional
from typing import List, Dict, Any


class GeneralActionTracker:
    """Tracks AI-generated plans and their execution status."""

    def __init__(self, project_root: str='.'):
        """Initialize the action tracker with project context."""
        self.project_root = os.path.abspath(project_root)
        self.tracker_file = os.path.join(self.project_root, '.omni',
            'action_tracker.json')
        self.action_memory = ActionMemoryManager()
        self.actions = []
        self._ensure_tracker_directory()
        self.load_actions()

    def _ensure_tracker_directory(self) ->None:
        """Ensure the .omni directory exists for tracking files."""
        omni_dir = os.path.join(self.project_root, '.omni')
        if not os.path.exists(omni_dir):
            os.makedirs(omni_dir)

    def add_action(self, action_type: str, file_path: str, element: str,
        status: str='pending', reason: str='') ->None:
        """Add a new action to track."""
        action = {'id': len(self.actions) + 1, 'type': action_type, 'file':
            file_path, 'element': element, 'status': status, 'reason':
            reason, 'created_at': datetime.now().isoformat(), 'updated_at':
            datetime.now().isoformat()}
        self.actions.append(action)
        self.save_actions()
        log_action_tracker_event(f'Added {action_type} action for {file_path}')

    def update_action_status(self, action_id: int, status: str, reason: str=''
        ) ->bool:
        """Update the status of a tracked action."""
        for action in self.actions:
            if action['id'] == action_id:
                action['status'] = status
                action['reason'] = reason
                action['updated_at'] = datetime.now().isoformat()
                self.save_actions()
                log_action_tracker_event(
                    f'Updated action {action_id} to {status}')
                return True
        return False

    def get_pending_actions(self) ->List[Dict]:
        """Get all pending actions."""
        return [action for action in self.actions if action['status'] ==
            'pending']

    def get_failed_actions(self) ->List[Dict]:
        """Get all failed actions."""
        return [action for action in self.actions if action['status'] ==
            'failed']

    def get_completed_actions(self) ->List[Dict]:
        """Get all completed actions."""
        return [action for action in self.actions if action['status'] ==
            'completed']

    def save_actions(self) ->None:
        """Save actions to the tracker file."""
        try:
            os.makedirs(os.path.dirname(self.tracker_file), exist_ok=True)
            with open(self.tracker_file, 'w') as f:
                json.dump(self.actions, f, indent=2)
        except Exception as e:
            log_action_tracker_event(f'Failed to save actions: {e}')

    def load_actions(self) ->None:
        """Load actions from the tracker file."""
        if not os.path.exists(self.tracker_file):
            self.actions = []
            return
        try:
            with open(self.tracker_file, 'r') as f:
                self.actions = json.load(f)
        except Exception as e:
            log_action_tracker_event(f'Failed to load actions: {e}')
            self.actions = []

    def clear_actions(self) ->None:
        """Clear all tracked actions."""
        self.actions = []
        self.save_actions()
        log_action_tracker_event('Cleared all actions')

    def get_action_summary(self) ->Dict[str, int]:
        """Get a summary of action statuses."""
        summary = {'pending': 0, 'completed': 0, 'failed': 0}
        for action in self.actions:
            status = action['status']
            if status in summary:
                summary[status] += 1
        return summary


class ActionTracker:
    """Tracks refactor actions and their execution status throughout the refactor process."""

    def __init__(self):
        self.action_memory = ActionMemoryManager()
        self.refactor_goal = None
        self.start_time = None

    def start_refactor(self, goal: str) ->None:
        """Record the start of a refactor operation."""
        self.refactor_goal = goal
        self.start_time = datetime.now()
        print(f'[INFO] Starting refactor: {goal}')

    def record_plan_generation(self, plan: Dict) ->None:
        """Record that a plan has been generated and add steps to action memory."""
        steps = plan.get('steps', [])
        print(f'[INFO] Generated refactor plan with {len(steps)} steps')
        for step in steps:
            self.action_memory.add_action(step, 'planned')

    def record_plan_validation(self, validated_plan: List[Dict]) ->None:
        """Record that a plan has been validated."""
        print(
            f'[INFO] Validated refactor plan with {len(validated_plan)} steps')
        for step in validated_plan:
            self.action_memory.add_action(step)

    def record_error(self, stage: str, error: str) ->None:
        """Record an error during the refactor process."""
        print(f'[ERROR] {stage}: {error}')

    def record_simulation(self, diff_text: str) ->None:
        """Record that changes have been simulated."""
        print('[INFO] Simulated proposed changes')

    def record_cancellation(self) ->None:
        """Record that the refactor was cancelled by the user."""
        print('[INFO] Refactor cancelled by user')

    def record_execution_start(self, plan: List[Dict]) ->None:
        """Record that execution has started."""
        print(f'[INFO] Starting execution of {len(plan)} steps')

    def record_step_success(self, step_index: int, step: Dict) ->None:
        """Record a successful step execution."""
        self.action_memory.update_action_status(step_index, 'success')

    def record_step_failure(self, step_index: int, step: Dict, error: str
        ) ->None:
        """Record a failed step execution."""
        self.action_memory.update_action_status(step_index, 'failed', error)

    def record_completion(self, success: bool) ->None:
        """Record that execution has completed."""
        status = 'completed' if success else 'failed'
        print(f'[INFO] Execution {status}')

    def get_action_history(self) ->List[Dict]:
        """Get the history of all actions."""
        return self.action_memory.get_actions()

    def clear_history(self) ->None:
        """Clear the action history."""
        self.action_memory.clear_actions()
