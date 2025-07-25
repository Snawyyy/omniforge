from typing import Optional
import logging


def log_edit_event(file_path: str, instruction: str, success: bool, error:
    Optional[str]=None) ->None:
    """
    Log an edit command event for audit trail purposes.
    
    Args:
        file_path: The path of the file that was edited
        instruction: The edit instruction provided by the user
        success: Whether the edit was successful
        error: Error message if the edit failed
    """
    if success:
        logging.info(f'Edit applied successfully to {file_path}: {instruction}'
            )
    else:
        logging.error(
            f'Edit failed for {file_path}: {instruction}. Error: {error}')


refactor_logger = logging.getLogger('omniforge.refactor')
refactor_logger.setLevel(logging.INFO)
if not refactor_logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    refactor_logger.addHandler(ch)


def log_refactor_complete(success: bool, goal: Optional[str]=None, duration:
    Optional[float]=None):
    """
    Logs the completion of a refactor operation.

    Args:
        success: Whether the refactor was successful.
        goal: Optional description of the refactor goal.
        duration: Optional time taken for the refactor in seconds.
    """
    status = 'SUCCESS' if success else 'FAILED'
    message = f'Refactor [{status}]'
    if goal:
        message += f' | Goal: {goal}'
    if duration is not None:
        message += f' | Duration: {duration:.2f}s'
    refactor_logger.info(message)
