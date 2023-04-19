import unittest

from infrastructure_builder.task_registry import TaskRegistry


@TaskRegistry.task("sampleTask", description="A sample task")
def sample_task():
    ...


@TaskRegistry.task("sampleTask2", description="Another sample task")
def sample_task2():
    ...


@TaskRegistry.task("compileTest", description="Compile + test")
def sample_task2():
    ...


class TestTaskRegistry(unittest.TestCase):

    def test_registry(self):
        # Correct spelling
        self.assertIsNotNone(TaskRegistry.get_task("sampleTask"))

        # Case-insensitive
        self.assertIsNotNone(TaskRegistry.get_task("sampletask"))

        # Beginning of name matches
        self.assertIsNotNone(TaskRegistry.get_task("compile"))

        # Beginning of name matches, case-insensitive
        self.assertIsNotNone(TaskRegistry.get_task("compilet"))

        # Wrong spelling
        self.assertIsNone(TaskRegistry.get_task("xxx"))

        # List of all tasks
        self.assertEqual("sampleTask   A sample task\nsampleTask2  Another sample task\ncompileTest  Compile + test",
                         TaskRegistry.format_task_descriptions())

    def test_call_task(self):
        TaskRegistry.get_task("sampleTask").execute()
