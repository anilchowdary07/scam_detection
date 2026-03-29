"""
Tasks module
"""
from . import easy, medium, hard

ALL_TASKS = [
    easy.TASK,
    medium.TASK,
    hard.TASK
]

def get_task(difficulty: str):
    """Get task by difficulty"""
    for task in ALL_TASKS:
        if task["difficulty"] == difficulty:
            return task
    return None

def get_all_tasks():
    """Get all tasks"""
    return ALL_TASKS
