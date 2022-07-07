import unittest

from infrastructure_builder.task_registry import TaskRegistry


@TaskRegistry.task("sampleTask", description="A sample task")
def sample_task():
    pass


@TaskRegistry.task("sampleTask2", description="Another sample task")
def sample_task2():
    pass


class TestTaskRegistry(unittest.TestCase):

    def test_registry(self):
        # Correct spelling
        self.assertIsNotNone(TaskRegistry.get_task("sampleTask"))

        # Case-insensitive
        self.assertIsNotNone(TaskRegistry.get_task("sampletask"))

        # Wrong spelling
        self.assertIsNone(TaskRegistry.get_task("xxx"))

        # List of all tasks
        self.assertEqual("sampleTask   A sample task\nsampleTask2  Another sample task",
                         TaskRegistry.format_task_descriptions())

    def test_call_task(self):
        TaskRegistry.get_task("sampleTask").execute()
