# Infrastructure Builder
Python tools to set up an infrastructure in a cloud. At the moment, AWS is the only supported cloud technology.

Usually a cloud setup has several resources which have to be set up in a specific sequence. While cloud environment support dependencies (e.g. AWS Cloudformation), it is sometimes not advisable to put all resources into a single configuration file. If you have multiple files, the Infrastructure Builder helps to put all these together. In addition, it is possible to add code which executes other tasks, e.g. building a Docker image, or modify cloud resources via API if unable to do so via configuration file. 

# Usage
Install package via `pip install infrastructure-builder[aws]`.

Create a file, e.g. `run.py`, which will host all tasks to set up a cloud infrastructure. A task might use AWS Cloudformation to do the work, or build a Docker image and upload it to a registry. The tasks to execute a given via command line::
```python
#!/usr/bin/env python
import argparse
import logging
import sys
from infrastructure_builder.task_registry import TaskRegistry

@TaskRegistry.task("setupSomething", description="Setup something in cloud environment")
def setup_something():
    pass

def main():
   valid_tasks = f"Valid tasks:\n{TaskRegistry.format_task_descriptions()}"
   parser = argparse.ArgumentParser(description="Build, run and deploy", 
                                    epilog=valid_tasks,
                                    formatter_class=argparse.RawTextHelpFormatter)
   parser.add_argument("tasks", metavar="task", type=str, nargs='+',
                       help="Task to execute")
   args = parser.parse_args(None if sys.argv[1:] else ["-h"])  # print help if no task was given

   for t in args.tasks:
      task_to_execute = TaskRegistry.get_task(t)
      if task_to_execute is None:
         logging.error(f"Unknown task {t}")
         logging.error(valid_tasks)
         return

      task_to_execute.execute()


if __name__ == "__main__":
   main()
```

## Execute external commands
Execute an external command and display its output in real-time:
```python
from infrastructure_builder.execute import execute_live

def docker_login(username: str, password: str, hostname: str):
    execute_live(["docker", "login",
                  "--username", username,
                  "--password-stdin",
                  hostname],
                 inp=password)
```

`execute` will do the same, but output is collected and will be returned after external command has exited.

## AWS
There are some helper classes to deal easily with AWS services:

| Class                    | Description                                       |
|--------------------------|---------------------------------------------------|
| ServiceBase              | Base class for an AWS service                     |
| Batch                    | AWS Batch related tasks                           |
| CloudFormation           | Create, update or delete a CloudFormation stack   |
| CodeArtifact             | CodeArtifact helper, e.g. get authorization token |
| Cognito                  | Cognito helper                                    |
| ElasticContainerRegistry | Docker registry, e.g. get authorization token     |
| Route53                  | Domain management, e.g. list managed domains      |
| SecurityTokenService     | AWS STS related tasks                             |

Any exceptions are coded in `exceptions.py`.

# Development
Source code is stored in directory `src`, unit tests in `tests`.

To install all dependencies, run `pip install -e .[aws]` (on zsh, `pip install -e .\[aws\]`). Make sure your pip version is up-to-date.

To execute the unit tests, run `python -m unittest discover -v`.
