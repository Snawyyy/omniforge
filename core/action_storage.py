"""
Action Storage Module

This module provides functionality to save and retrieve actions using either
a disk-based or database-based backend. It offers a unified interface for
persistent storage of action history.
"""

import os
import json
import sqlite3
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from contextlib import contextmanager


class ActionStorageBackend(ABC):
    """Abstract base class for action storage backends."""
    
    @abstractmethod
    def save_action(self, action: Dict[str, Any]) -> None:
        """Save an action to the storage backend."""
        pass

    @abstractmethod
    def get_actions(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve actions from the storage backend."""
        pass

    @abstractmethod
    def clear_actions(self) -> None:
        """Clear all actions from the storage."""
        pass


class DiskActionStorage(ActionStorageBackend):
    """Disk-based action storage implementation."""
    
    def __init__(self, file_path: str = "actions.jsonl"):
        self.file_path = file_path
        
    def save_action(self, action: Dict[str, Any]) -> None:
        """Save an action to a JSON lines file."""
        action['_timestamp'] = datetime.utcnow().isoformat() + 'Z'
        with open(self.file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(action) + '\n')

    def get_actions(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve actions from the JSON lines file."""
        actions = []
        if not os.path.exists(self.file_path):
            return actions
            
        with open(self.file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if limit:
                lines = lines[-limit:]
            for line in lines:
                try:
                    actions.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    # Skip malformed lines
                    continue
        return actions

    def clear_actions(self) -> None:
        """Clear all actions by deleting the file."""
        if os.path.exists(self.file_path):
            os.remove(self.file_path)


class DatabaseActionStorage(ActionStorageBackend):
    """Database-based action storage implementation using SQLite."""
    
    def __init__(self, db_path: str = "actions.db"):
        self.db_path = db_path
        self._initialize_database()

    def _initialize_database(self) -> None:
        """Initialize the database with the required table."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    details TEXT NOT NULL
                )
            """)

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def save_action(self, action: Dict[str, Any]) -> None:
        """Save an action to the database."""
        action_type = action.get('type', 'unknown')
        details = json.dumps({k: v for k, v in action.items() if k != 'type'})
        
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO actions (timestamp, action_type, details) VALUES (?, ?, ?)",
                (datetime.utcnow().isoformat() + 'Z', action_type, details)
            )

    def get_actions(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve actions from the database."""
        query = "SELECT timestamp, action_type, details FROM actions ORDER BY timestamp DESC"
        if limit:
            query += f" LIMIT {limit}"
            
        with self._get_connection() as conn:
            cursor = conn.execute(query)
            rows = cursor.fetchall()
            
        actions = []
        for row in rows:
            try:
                details = json.loads(row[2])
                action = {'type': row[1], **details, '_timestamp': row[0]}
                actions.append(action)
            except json.JSONDecodeError:
                # Skip malformed entries
                continue
        
        # Return in chronological order
        return list(reversed(actions))

    def clear_actions(self) -> None:
        """Clear all actions from the database."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM actions")


class ActionStorage:
    """Main action storage interface supporting multiple backends."""
    
    def __init__(self, backend_type: str = "disk", **kwargs):
        """
        Initialize the action storage with the specified backend.
        
        Args:
            backend_type: Either "disk" or "database"
            **kwargs: Additional arguments for the backend constructor
        """
        if backend_type == "disk":
            self.backend = DiskActionStorage(**kwargs)
        elif backend_type == "database":
            self.backend = DatabaseActionStorage(**kwargs)
        else:
            raise ValueError(f"Unsupported backend type: {backend_type}")

    def save_action(self, action_type: str, **details) -> None:
        """
        Save an action to the storage.
        
        Args:
            action_type: Type of the action (e.g., "edit", "refactor", "create")
            **details: Additional details about the action
        """
        action = {"type": action_type, **details}
        self.backend.save_action(action)

    def get_actions(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve actions from the storage.
        
        Args:
            limit: Maximum number of actions to retrieve (None for all)
            
        Returns:
            List of actions in chronological order
        """
        return self.backend.get_actions(limit)

    def clear_actions(self) -> None:
        """Clear all actions from the storage."""
        self.backend.clear_actions()

    def get_recent_actions(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most recent N actions.
        
        Args:
            count: Number of recent actions to retrieve
            
        Returns:
            List of recent actions
        """
        return self.get_actions(limit=count)