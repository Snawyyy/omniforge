import json
import os
from typing import List, Dict, Optional
from rag_manager import RAGManager
from datetime import datetime
from typing import List, Dict, Any, Optional


class MemoryManager:
    """Manages persistent chat memory, look data, and RAG integration via JSON."""

    def __init__(self, memory_file: str):
        self.memory_file = memory_file
        self.memory: Dict[str, List] = self.load_memory()
        self.rag_manager = RAGManager()

    def load_memory(self) ->Dict[str, List]:
        try:
            with open(self.memory_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            default = {'chat': [], 'look': [], 'actions': [],
                'refactor_plans': []}
            self.save_memory(default)
            return default
        except json.JSONDecodeError:
            print('[yellow]Invalid memory file. Resetting.[/]')
            return {'chat': [], 'look': [], 'actions': [], 'refactor_plans': []
                }

    def save_memory(self, memory: Optional[Dict[str, List]]=None) ->None:
        if memory is None:
            memory = self.memory
        with open(self.memory_file, 'w') as f:
            json.dump(memory, f, indent=4)

    def add_message(self, role: str, content: str) ->None:
        """
        Add a message to the chat history and save immediately.
        
        Args:
            role: The role of the message sender (e.g., 'user', 'assistant')
            content: The message content
        """
        self.memory['chat'].append({'role': role, 'content': content})
        self.save_memory()

    def add_chat_message(self, role: str, content: str) ->None:
        """
        Add a message to the chat history and save immediately.
        This is an alias for add_message to maintain compatibility.
        
        Args:
            role: The role of the message sender (e.g., 'user', 'assistant')
            content: The message content
        """
        self.add_message(role, content)

    def add_action(self, action_type: str, details: Dict) ->None:
        """
        Add an action to the action history and save immediately.
        
        Args:
            action_type: The type of action (e.g., 'edit', 'create', 'refactor')
            details: Dictionary containing action details
        """
        action_record = {'type': action_type, 'timestamp': datetime.now().
            isoformat(), 'details': details}
        self.memory.setdefault('actions', []).append(action_record)
        self.save_memory()

    def get_recent_actions(self, limit: int=10) ->List[Dict]:
        """
        Get the most recent actions from the action history.
        
        Args:
            limit: Maximum number of actions to return
            
        Returns:
            List of recent action records
        """
        actions = self.memory.get('actions', [])
        return actions[-limit:] if len(actions) > limit else actions

    def add_refactor_plan(self, plan: Dict, result: Optional[Dict]=None
        ) ->None:
        """
        Store a refactor plan and its result in memory.
        
        Args:
            plan: The refactor plan dictionary
            result: Optional result of the refactor execution
        """
        plan_record = {'timestamp': datetime.now().isoformat(), 'plan':
            plan, 'result': result}
        self.memory.setdefault('refactor_plans', []).append(plan_record)
        self.save_memory()

    def get_recent_refactor_plans(self, limit: int=5) ->List[Dict]:
        """
        Get the most recent refactor plans from memory.
        
        Args:
            limit: Maximum number of plans to return
            
        Returns:
            List of recent refactor plan records
        """
        plans = self.memory.get('refactor_plans', [])
        return plans[-limit:] if len(plans) > limit else plans

    def add_look_data(self, file_path: str, content: str) ->None:
        """
    Adds a watched item (directory or file) to memory, distinguishing its type.

    This method stores structured data that differentiates between a project
    directory (containing a manifest) and a single file (containing its content).
    It also prevents duplicate entries by updating existing ones.

    Args:
        file_path: The path to the directory or file.
        content: The manifest for a directory or the content for a file.
    """
        item_type = 'directory' if os.path.isdir(file_path) else 'file'
        for item in self.memory['look']:
            if item.get('file') == file_path:
                item['content'] = content
                item['type'] = item_type
                self.save_memory()
                return
        self.memory['look'].append({'type': item_type, 'file': file_path,
            'content': content})
        self.save_memory()
        if item_type == 'file':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                self.rag_manager.add_documents([file_content], [{'file':
                    file_path}])
            except Exception as e:
                print(
                    f'[yellow]Warning: Could not add {file_path} to RAG index: {e}[/]'
                    )

    def add_file_to_memory(self, file_path: str) ->None:
        """
        Add a file to memory by reading its content and storing it.
        
        Args:
            file_path: The path to the file to add to memory
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.add_look_data(file_path, content)
        except Exception as e:
            print(
                f'[yellow]Warning: Could not add {file_path} to memory: {e}[/]'
                )

    def get_project_root(self) ->Optional[str]:
        """
        Finds the root directory of the project currently in memory.

        The project root is defined as the first item in the 'look' memory
        that is of type 'directory'.

        Returns:
            The absolute path to the project root directory, or None if not found.
        """
        for item in self.memory.get('look', []):
            if item.get('type') == 'directory':
                return item.get('file')
        return None

    def get_memory_context(self, selected_files: Optional[List[str]]=None
        ) ->str:
        """
        Dynamically builds the context using RAG and chat history.

        It retrieves relevant file content from the RAG index based on the latest
        user query, includes project manifests for directories, and appends the
        recent chat history. Can optionally filter to only include specified files.

        Args:
            selected_files: Optional list of file paths to include in context.
                           If None, includes all files in memory.
        """
        context = ''
        for look in self.memory.get('look', []):
            path = look.get('file')
            if path and os.path.isdir(path):
                content = look.get('content', '')
                context += (
                    f'--- Project Manifest for {path} ---\n{content}\n\n')
        if selected_files is not None:
            for look in self.memory.get('look', []):
                path = look.get('file')
                if path and os.path.isfile(path) and path in selected_files:
                    content = look.get('content', '')
                    context += f'--- File: {path} ---\n{content}\n\n'
        last_user_message = next((msg['content'] for msg in reversed(self.
            memory.get('chat', [])) if msg['role'] == 'user'), None)
        if last_user_message:
            rag_results = self.search_rag(last_user_message, k=3)
            if rag_results:
                context += '--- Relevant context from RAG ---\n'
                for doc, score, meta in rag_results:
                    file_path = meta.get('file', 'Unknown source')
                    if selected_files is None or file_path in selected_files:
                        context += (
                            f'Source: {file_path} (Score: {score:.4f})\n')
                        context += f'Content: {doc}\n---\n'
                context += '\n'
        for msg in self.memory.get('chat', []):
            context += f"{msg['role'].capitalize()}: {msg['content']}\n"
        action_history = self.memory.get('action_history', [])
        if action_history:
            context += '\n--- Action History ---\n'
            for action in action_history:
                context += f'- {action}\n'
        return context.strip()

    def clear_memory(self) ->None:
        self.memory = {'chat': [], 'look': [], 'actions': [],
            'refactor_plans': []}
        self.save_memory()
        self.rag_manager.clear_index()

    def search_rag(self, query: str, k: int=3) ->List[tuple]:
        """
        Search the RAG index for relevant documents.
        
        Args:
            query: The search query
            k: Number of results to return
            
        Returns:
            List of (document_content, score, metadata) tuples
        """
        return self.rag_manager.search(query, k)

    def add_refactor_result(self, result: Dict) ->None:
        """
        Add a refactor result to the memory.
        
        Args:
            result: Dictionary containing the refactor result details.
        """
        self.memory.setdefault('refactor_results', []).append(result)
        self.save_memory()


class ActionMemoryManager:
    """Manages memory for tracking refactor actions and their execution status."""

    def __init__(self):
        self.actions: List[Dict[str, Any]] = []

    def add_action(self, step: Dict[str, Any], status: str='pending', error:
        Optional[str]=None) ->None:
        """
        Add an action to memory.
        
        Args:
            step: The refactor step dictionary
            status: Execution status ("pending", "success", "failed")
            error: Error message if failed
        """
        action_entry = {'step': step.copy(), 'status': status, 'error':
            error, 'timestamp': self._get_timestamp()}
        self.actions.append(action_entry)

    def update_action_status(self, step_index: int, status: str, error:
        Optional[str]=None) ->None:
        """
        Update the status of an existing action.
        
        Args:
            step_index: Index of the step in the plan
            status: New status ("success", "failed")
            error: Error message if failed
        """
        if 0 <= step_index < len(self.actions):
            self.actions[step_index]['status'] = status
            if error:
                self.actions[step_index]['error'] = error
            self.actions[step_index]['timestamp'] = self._get_timestamp()

    def get_actions(self) ->List[Dict[str, Any]]:
        """Get all tracked actions."""
        return self.actions.copy()

    def clear_actions(self) ->None:
        """Clear all actions from memory."""
        self.actions.clear()

    def _get_timestamp(self) ->str:
        """Get current timestamp."""
        return datetime.now().isoformat()
