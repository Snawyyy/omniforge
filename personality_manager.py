import json
from typing import Dict, List, Optional

class PersonalityManager:
    """Manages AI personalities via JSON config."""

    def __init__(self, config_file: str):
        self.config_file = config_file
        self.personalities: List[Dict[str, str]] = self.load_personalities()
        self.current_personality: Optional[str] = "default"  # Default

    def load_personalities(self) -> List[Dict[str, str]]:
        """Load personalities from JSON; auto-create if missing."""
        default = [{"name": "default", "description": "Helpful assistant", "system_prompt": "You are a helpful AI assistant."}]
        default_gui = {
            "gui_enabled": True,
            "wake_word": "Jarvis",
            "overlay_opacity": 0.8,
            "font_size": 16
        }
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
                if "personalities" not in data:
                    data["personalities"] = default
                if "gui_enabled" not in data:
                    data.update(default_gui)
                    self.save_personalities(data["personalities"])  # Save with defaults
                
                return data["personalities"]
        except FileNotFoundError:
            self.save_personalities(default)
            return default
        except json.JSONDecodeError:
            print("[yellow]Invalid config. Resetting to default.[/]")
            self.save_personalities(default)
            return default

    def save_personalities(self, personalities: List[Dict[str, str]]) -> None:
        """Save with GUI config."""
        data = {"personalities": personalities}
        data.update({"gui_enabled": True, "wake_word": "Jarvis", "overlay_opacity": 0.8, "font_size": 16})  # Defaults
        with open(self.config_file, 'w') as f:
            json.dump(data, f, indent=4)

    def add_personality(self, name: str, description: str, system_prompt: str) -> None:
        """Add a new personality."""
        self.personalities.append({"name": name, "description": description, "system_prompt": system_prompt})
        self.save_personalities(self.personalities)

    def list_personalities(self) -> List[Dict[str, str]]:
        """List all personalities."""
        return self.personalities

    def set_current_personality(self, name: str) -> bool:
        """Set the current personality."""
        for p in self.personalities:
            if p["name"] == name:
                self.current_personality = name
                return True
        return False

    def get_current_personality(self) -> Dict[str, str]:
        """Get the current personality dict."""
        for p in self.personalities:
            if p["name"] == self.current_personality:
                return p
        return {}  # Fallback