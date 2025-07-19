import json
import os
from typing import List, Dict, Optional

class MemoryManager:
    """Manages persistent chat memory and look data via JSON."""

    def __init__(self, memory_file: str):
        self.memory_file = memory_file
        self.memory: Dict[str, List] = self.load_memory()

    def load_memory(self) -> Dict[str, List]:
        try:
            with open(self.memory_file, 'r') as f: return json.load(f)
        except FileNotFoundError:
            default = {"chat": [], "look": []}
            self.save_memory(default); return default
        except json.JSONDecodeError:
            print("[yellow]Invalid memory file. Resetting.[/]"); return {"chat": [], "look": []}

    def save_memory(self, memory: Optional[Dict[str, List]] = None) -> None:
        if memory is None: memory = self.memory
        with open(self.memory_file, 'w') as f: json.dump(memory, f, indent=4)

    def add_message(self, role: str, content: str) -> None:
        self.memory["chat"].append({"role": role, "content": content}); self.save_memory()

    def add_look_data(self, file_path: str, content: str) -> None:
        self.memory["look"].append({"file": file_path, "content": content}); self.save_memory()

    def get_memory_context(self) -> str:
        context = ""
        for look in self.memory["look"]: context += f"--- Content of {look['file']} ---\n{look['content']}\n\n"
        for msg in self.memory["chat"]: context += f"{msg['role'].capitalize()}: {msg['content']}\n"
        return context.strip()
    
    def get_project_root(self) -> Optional[str]:
        """Finds the first directory path in the 'look' memory."""
        for item in self.memory.get('look', []):
            path = item['file']
            if os.path.isdir(path):
                return path
        return None

    def clear_memory(self) -> None:
        self.memory = {"chat": [], "look": []}; self.save_memory()