# Infrastructure Builder
Python tools to set up an infrastructure in the cloud. At the moment, AWS is the only supported cloud technology.

Usually a cloud setup has several resources which have to be set up in a specific sequence. While cloud environment supports dependencies (e.g. AWS Cloudformation), it is sometimes not advisable to put all resources into a single configuration file. If you have multiple files, the Infrastructure Builder helps to put all these together. In addition, it is possible to add code which executes other tasks, e.g. building a Docker image, or modify cloud resources via API if unable to do so via a configuration file. 

# Usage
Install package via `pip install infrastructure-builder[aws]`.

Create a file, e.g. `run.py`, which will host all tasks to set up a cloud infrastructure. A task might use AWS Cloudformation to do the work, or build a Docker image and upload it to a registry. The tasks to execute a given via command line::
```python
#!/usr/bin/env python
import logging
from infrastructure_builder.task_registry import TaskRegistry

@TaskRegistry.task("setupSomething", description="Set up something in cloud environment")
def setup_something():
    pass

def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    TaskRegistry.execute_from_command_line()

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
| LambdaFunction           | Lambda Function helper                            |
| Route53                  | Domain management, e.g. list managed domains      |
| SecurityTokenService     | AWS STS related tasks                             |
| Step Functions           | Step Functions helper                             |
| Systems Manager          | Systems Manager helper                            |

Any exceptions are coded in `exceptions.py`.

# Development
Source code is stored in directory `src`, unit tests in `tests`.

To install all dependencies, run `pip install -e .[aws]` (on zsh, `pip install -e .\[aws\]`; with uv, `uv pip install -e .[aws]`). Make sure your pip version is up-to-date.

To execute the unit tests, run `python -m unittest discover -v` (with uv, `uv run -m unittest discover -v`).

## Local environment with Linux and AWS
Script to set up a local environment:
```shell
#!/usr/bin/env bash
REPOSITORY_TOKEN=$(aws codeartifact get-authorization-token --domain xxx --domain-owner yyy --query authorizationToken --output text)
REPOSITORY_URL=$(aws codeartifact get-repository-endpoint --domain xxx --domain-owner yyy --repository common --format pypi --query repositoryEndpoint --output text)
PIP_REPOSITORY=https://aws:${REPOSITORY_TOKEN}@${REPOSITORY_URL:8}simple/
pip install --index-url "$PIP_REPOSITORY" -e .[aws]
```

## Local environment with Windows and AWS
Script to set up a local environment:
```shell
$Env:REPOSITORY_TOKEN = aws codeartifact get-authorization-token --domain xxx --domain-owner yyy --query authorizationToken --output text
$Env:REPOSITORY_URL= aws codeartifact get-repository-endpoint --domain xxx --domain-owner yyy --repository common --format pypi --query repositoryEndpoint --output text
$Env:PIP_REPOSITORY = "https://aws:$($Env:REPOSITORY_TOKEN)@$($Env:REPOSITORY_URL.Substring(8))simple/"
pip install --index-url "$Env:PIP_REPOSITORY" -e .[aws]
```
