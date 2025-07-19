import json
import os
from typing import List, Dict, Optional


class MemoryManager:
    """Manages persistent chat memory and look data via JSON."""

    def __init__(self, memory_file: str):
        self.memory_file = memory_file
        self.memory: Dict[str, List] = self.load_memory()

    def load_memory(self) ->Dict[str, List]:
        try:
            with open(self.memory_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            default = {'chat': [], 'look': []}
            self.save_memory(default)
            return default
        except json.JSONDecodeError:
            print('[yellow]Invalid memory file. Resetting.[/]')
            return {'chat': [], 'look': []}

    def save_memory(self, memory: Optional[Dict[str, List]]=None) ->None:
        if memory is None:
            memory = self.memory
        with open(self.memory_file, 'w') as f:
            json.dump(memory, f, indent=4)

    def add_message(self, role: str, content: str) ->None:
        self.memory['chat'].append({'role': role, 'content': content})
        self.save_memory()

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

    def get_memory_context(self) ->str:
        """
    Dynamically builds the context. For files in 'look' memory, it reads
    their current content from disk. For directories, it uses the stored
    manifest. Appends the chat history.
    """
        context = ''
        for look in self.memory.get('look', []):
            path = look.get('file')
            if not path:
                continue
            if os.path.isfile(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    context += f'--- Content of {path} ---\n{content}\n\n'
                except Exception:
                    context += f'--- Content of {path} (UNREADABLE) ---\n\n'
            elif os.path.isdir(path):
                content = look.get('content', '')
                if isinstance(content, tuple):
                    content = content[0]
                context += (
                    f'--- Project Manifest for {path} ---\n{content}\n\n')
        for msg in self.memory.get('chat', []):
            context += f"{msg['role'].capitalize()}: {msg['content']}\n"
        return context.strip()

    def get_project_root(self) ->Optional[str]:
        """
    Finds the most recently added directory path in the 'look' memory.
    This is assumed to be the project root, prioritizing the latest context.
    """
        for item in reversed(self.memory.get('look', [])):
            path = item.get('file')
            if path and os.path.isdir(path):
                return path
        return None

    def clear_memory(self) ->None:
        self.memory = {'chat': [], 'look': []}
        self.save_memory()
