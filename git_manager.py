import subprocess
import os
from typing import List, Optional, Union


class GitManager:
    """
    Encapsulates Git-related logic for a specific repository.

    This class provides methods to perform common Git operations such as
    checking status, getting diffs, staging, committing, and pushing changes.
    It relies on the Git command-line tool being installed and accessible
    in the system's PATH.
    """

    def __init__(self, repo_path: str):
        """
        Initializes the GitManager for a given repository path.

        Args:
            repo_path: The absolute or relative path to the Git repository.

        Raises:
            ValueError: If the provided path is not a valid Git repository.
        """
        if not os.path.isdir(os.path.join(repo_path, '.git')):
            raise ValueError(
                f"The path '{repo_path}' is not a valid Git repository.")
        self.repo_path = repo_path

    def _run_command(self, command: List[str]) ->str:
        """
        Executes a Git command in the repository's directory.

        Args:
            command: A list of command arguments, starting with 'git'.

        Returns:
            The standard output of the command as a string.

        Raises:
            subprocess.CalledProcessError: If the command returns a non-zero exit code.
        """
        try:
            result = subprocess.run(command, cwd=self.repo_path, check=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                encoding='utf-8')
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            error_message = (
                f"Git command failed: {' '.join(command)}\nError: {e.stderr.strip()}"
                )
            raise subprocess.CalledProcessError(e.returncode, e.cmd, output
                =e.stdout, stderr=error_message) from e

    def get_status(self) ->str:
        """
        Gets the repository status in a condensed format.

        Uses `git status --porcelain` for a machine-readable output.

        Returns:
            A string representing the repository's status.
        """
        return self._run_command(['git', 'status', '--porcelain'])
        
    def get_changed_files(self) -> List[str]:
        """
        Gets a list of all changed (modified, added, deleted, untracked, renamed, or copied) files.

        This parses the output of `git status --porcelain`, which provides a stable,
        machine-readable format.

        Returns:
            A list of file paths relative to the repository root. For renamed or
            copied files, it returns the new path.
        """
        status_output = self.get_status()
        if not status_output:
            return []
        
        changed_files = []
        for line in status_output.splitlines():
            if len(line) < 3:  # Skip malformed lines
                continue
                
            # Git status porcelain format: XY filename
            # X = index status, Y = working tree status
            index_status = line[0]
            worktree_status = line[1]
            
            # The filename starts after the two status characters and a space
            # But let's be more defensive about finding where the filename actually starts
            filename_start = 2
            while filename_start < len(line) and line[filename_start] == ' ':
                filename_start += 1
                
            if filename_start >= len(line):
                continue  # Skip if no filename found
                
            path_info = line[filename_start:]
            
            # Check if either index or working tree status indicates rename/copy
            if index_status in ('R', 'C') or worktree_status in ('R', 'C'):
                if ' -> ' in path_info:
                    _, new_path = path_info.split(' -> ', 1)  # Use maxsplit=1 for safety
                    changed_files.append(new_path.strip())
                else:
                    # Fallback if format is unexpected
                    changed_files.append(path_info.strip())
            else:
                changed_files.append(path_info.strip())
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(changed_files))

    def get_diff(self, file_path: Optional[str]=None, staged: bool=False
        ) ->str:
        """
        Gets the diff of changes in the repository.

        Args:
            file_path: Optional. Path to a specific file to diff.
            staged: If True, shows the diff for staged changes (`--cached`).
                    Otherwise, shows the diff for unstaged changes.

        Returns:
            The git diff output as a string.
        """
        cmd = ['git', 'diff']
        if staged:
            cmd.append('--cached')
        if file_path:
            cmd.append('--')
            cmd.append(file_path)
        return self._run_command(cmd)

    def add(self, files: Union[str, List[str]]) ->None:
        """
    Stages one or more files, handling each one individually for robustness.

    This approach prevents a single invalid file path from causing the
    entire 'git add' operation to fail. Warnings will be printed for any
    files that could not be staged.

    Args:
        files: A single file path or a list of file paths to stage.
               Can also be '.' to stage all changes.
    """
        if isinstance(files, str):
            files = [files]
        for file_path in files:
            try:
                cmd = ['git', 'add', '--', file_path]
                self._run_command(cmd)
            except subprocess.CalledProcessError as e:
                print(
                    f"Warning: Could not stage file '{file_path}'. Git reported: {e.stderr}"
                    )

    def commit(self, message: str) ->str:
        """
        Commits staged changes with a given message.

        Args:
            message: The commit message.

        Returns:
            The stdout from the git commit command.
        """
        return self._run_command(['git', 'commit', '-m', message])

    def push(self, remote: str='origin', branch: Optional[str]=None) ->str:
        """
        Pushes commits to a remote repository.

        Args:
            remote: The name of the remote to push to (default: 'origin').
            branch: The branch to push. If None, uses the current branch.

        Returns:
            The stdout from the git push command.
        """
        if branch is None:
            branch = self.get_current_branch()
        return self._run_command(['git', 'push', remote, branch])

    def get_current_branch(self) ->str:
        """
        Determines the current active branch name.

        Returns:
            The name of the current branch.
        """
        return self._run_command(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
