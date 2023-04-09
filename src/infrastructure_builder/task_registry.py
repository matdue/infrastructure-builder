import argparse
import logging
import sys
from dataclasses import dataclass
from typing import Callable, Optional


logger = logging.getLogger(__name__)


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

    @classmethod
    def execute_from_command_line(cls) -> None:
        """
        Scans the command line arguments and executes all tasks that have been passed.
        If there are no arguments, a brief help will be printed, plus a list of all valid tasks.
        """
        valid_tasks = f"Valid tasks:\n{cls.format_task_descriptions()}"
        parser = argparse.ArgumentParser(description="Build, run and deploy", epilog=valid_tasks,
                                         formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument("tasks", metavar="task", type=str, nargs='+',
                            help="Task to execute")
        args = parser.parse_args(None if sys.argv[1:] else ["-h"])  # print help if no task was given

        for t in args.tasks:
            task_to_execute = cls.get_task(t)
            if task_to_execute is None:
                logging.error(f"Unknown task {t}")
                logging.error(valid_tasks)
                return

            task_to_execute.execute()
