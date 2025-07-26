import json
from typing import List, Dict, Any
from .model_client import send_prompt_to_model
from .prompt_builder import build_refactor_goal_prompt
from context.context_manager import get_project_context_summary


class Refactor:

    def __init__(self, goal: str):
        self.goal = goal
        self.plan = None

    def generate_plan(self):
        context_summary = get_project_context_summary()
        prompt = build_refactor_goal_prompt(self.goal, context_summary)
        try:
            plan_json = self.request_structured_plan(prompt)
            self.plan = self.validate_steps(plan_json.get('steps', []))
        except Exception as e:
            raise Exception(
                f'Failed to generate and validate refactor plan: {e}')

    def request_structured_plan(self, prompt: str) ->Dict[str, Any]:
        response = send_prompt_to_model(prompt)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {'plan': response}

    def validate_steps(self, steps: List[Dict[str, Any]]) ->List[Dict[str, Any]
        ]:
        if not isinstance(steps, list) or not steps:
            raise ValueError('Steps must be a non-empty list.')
        required_fields = {'type', 'file', 'description'}
        modification_types = {'edit', 'add', 'delete', 'refactor'}
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                raise ValueError(f'Step {i} must be a dictionary.')
            missing_fields = required_fields - set(step.keys())
            if missing_fields:
                raise ValueError(
                    f'Step {i} is missing required fields: {missing_fields}')
            if step['type'] not in modification_types:
                raise ValueError(
                    f"Step {i} has an invalid type '{step['type']}'. Must be one of {modification_types}."
                    )
            if not isinstance(step['file'], str) or not step['file'].strip():
                raise ValueError(f'Step {i} has an invalid file path.')
            if not isinstance(step['description'], str) or not step[
                'description'].strip():
                raise ValueError(f'Step {i} has an invalid description.')
            if step['type'
                ] == 'edit' and 'search' not in step and 'line_number' not in step:
                raise ValueError(
                    f"Edit step {i} must include either 'search' or 'line_number'."
                    )
            if step['type'] == 'add' and 'content' not in step:
                raise ValueError(f"Add step {i} must include 'content'.")
        return steps

    def get_plan(self):
        return self.plan
