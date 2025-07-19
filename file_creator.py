"""
Generated file.
"""
import os
"""
FileCreator - A utility for creating files.

This module provides a simple, encapsulated way to create files,
ensuring that their parent directories exist before writing.
"""


class FileCreator:
    """
    A utility class to handle the creation of new files.
    """

    @staticmethod
    def create(file_path: str, content: str) ->None:
        """
        Creates a file at the specified path with the given content.

        This method will automatically create any necessary parent
        directories for the file path.

        Args:
            file_path: The full path where the file should be created.
            content: The string content to write to the file.

        Raises:
            IOError: If there is an error creating the directories or writing the file.
        """
        try:
            directory = os.path.dirname(file_path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except (IOError, OSError) as e:
            raise IOError(f"Failed to create file '{file_path}': {e}") from e
