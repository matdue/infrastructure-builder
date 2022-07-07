from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class Task:
    name: str
    description: str
    execute: Callable


class TaskRegistry:
    """
    Registry for tasks.
    """
    tasks = {}

    @classmethod
    def task(cls, name: str, description: str):
        """
        Decorator to mark a function as a task.

        :param name: The task name
        :param description: The task description
        """
        def register_task(func):
            cls.tasks[name] = Task(name, description, func)
            return func

        return register_task

    @classmethod
    def get_task(cls, name: str) -> Optional[Task]:
        """
        Look up a task and do not care about case-sensitivity.

        :param name: The task name to look up
        :return: task or None if no matching task was found
        """
        name_lower = name.lower()
        real_task_name = next((key for key in cls.tasks if key.lower() == name_lower), None)
        return cls.tasks.get(real_task_name, None)

    @classmethod
    def format_task_descriptions(cls) -> str:
        """
        Create a multiline string with all task and its descriptions. Useful for printing all registered tasks to a
        console.

        :return: String with all tasks and descriptions
        """
        # Determine the length of the longest task name in order to print a table
        all_tasks = cls.tasks.values()
        max_task_name_len = max(len(t.name) for t in all_tasks)
        task_descriptions = [f"{t.name: <{max_task_name_len}}  {t.description}" for t in all_tasks]
        return "\n".join(task_descriptions)
