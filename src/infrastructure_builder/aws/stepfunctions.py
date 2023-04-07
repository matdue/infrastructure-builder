import logging
import re
from datetime import datetime, timezone, timedelta
from functools import cached_property
from time import sleep

import boto3

from infrastructure_builder.aws.service_base import ServiceBase
from infrastructure_builder.exceptions import BuilderError


class StepFunctions(ServiceBase):
    """
    Helper functions for AWS Step Functions
    """
    def __init__(self, session: boto3.Session = None, region: str = None):
        super().__init__(session, region)

    @cached_property
    def client(self):
        """
        Returns a Boto3 client for AWS Step Functions. The client object is cached.
        :return: A Boto3 client for AWS Step Functions
        """
        return self.session.client("stepfunctions", region_name=self.region)

    def execute(self, state_machine_arn: str, input_data: str = None, timeout: int = 15,
                wait_until_completed: bool = True) -> str:
        """
        Executes a state machine. The function returns either immediately, or it will wait until the state machine has
        finished.

        If wait_until_completed is True, any state changes will be logged via Python logging module at info level.

        :param state_machine_arn: The ARN of the state machine.
        :param input_data: The JSON input data.
        :param timeout: The maximum time to wait for the job to finish (in minutes). If the job takes more time, an
            BuilderError exception will be raised. The job will continue to run, it will not be aborted!
        :param wait_until_completed: If False, this method will return immediately after submit, else will wait until
            the job has finished or the timeout has been reached.
        :return: Job ID
        """
        result = self.client.start_execution(stateMachineArn=state_machine_arn, input=input_data)
        execution_arn = result["executionArn"]
        if not wait_until_completed:
            return execution_arn

        logging.info("State submitted, now waiting until completed.")
        last_status = None
        start = datetime.now(timezone.utc) - timedelta(seconds=30)
        end = start + timedelta(minutes=timeout)
        while True:
            if datetime.now(timezone.utc) > end:
                raise BuilderError("Timeout")

            execution_description = self.client.describe_execution(executionArn=execution_arn)
            status = execution_description["status"]
            if status != last_status:
                last_status = status
                logging.info(f"Status: {status}")
            if status not in ["RUNNING"]:
                break

            sleep(5)

        if last_status != "SUCCEEDED":
            if "error" in execution_description:
                logging.info(f"Error: {execution_description['error']}")
            if "cause" in execution_description:
                logging.info(f"Cause: {execution_description['cause']}")

        # https://region.console.aws.amazon.com/states/home?region=region#/v2/executions/details/arn:...
        aws_region = re.match(r"arn:aws:states:(.*?):.*", execution_arn).group(1)
        url = f"https://{aws_region}.console.aws.amazon.com/states/home?region={aws_region}#/v2/executions/details/{execution_arn}"
        logging.info(f"Execution details in AWS console: {url}")

        return execution_arn
