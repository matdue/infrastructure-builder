# Infrastructure builder
Tools to set up an infrastructure in a cloud. At the moment, AWS is the only supported cloud technology.

## Technologies
Install [Python 3.9.x](https://www.python.org/downloads/)

## Project setup
1. Initialize python virtual environment, i.e. change to project directory and create virtual environment
    ```shell
    python -m venv .venv
    ```
1. Activate virtual environment
    ```shell
    source .venv/bin/activate
    ```
1. Install package
    ```shell
    pip install -e .[aws]
    pip install -e .\[aws\]  # zsh, e.g. MacOS
    ```

# Usage
Install package via `pip install infrastructure-builder`. If you would like to install AWS related tools, too, execute `pip install infrastructure-builder[aws]`.

## Tasks
Mark functions as tasks and execute them from command line:
```python
#!/usr/bin/env python
import argparse
import logging
import sys
from infrastructure_builder.task_registry import TaskRegistry

@TaskRegistry.register("setupSomething", description="Setup something in cloud environment")
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
