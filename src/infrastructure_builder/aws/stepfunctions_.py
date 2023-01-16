import logging
import re
from datetime import datetime, timezone, timedelta
from functools import cached_property
from time import sleep

import boto3

from infrastructure_builder.aws.exceptions import BuilderError
from infrastructure_builder.aws.service_base import ServiceBase


class StepFunctions(ServiceBase):
    def __init__(self, session: boto3.Session = None, region: str = None):
        super().__init__(session, region)

    @cached_property
    def client(self):
        return self.session.client("stepfunctions", region_name=self.region)

    def execute(self, state_machine_arn: str, input_data: str = None, timeout=15, wait_until_completed=True):
        """
        Executes a state machine.

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

        # https://eu-central-1.console.aws.amazon.com/states/home?region=eu-central-1#/v2/executions/details/arn:aws:states:eu-central-1:123456789012:execution:xyz:7f761627-cd3a-3bd0-289f-a0a847f1dcd4
        aws_region = re.match(r"arn:aws:states:(.*?):.*", execution_arn).group(1)
        url = f"https://{aws_region}.console.aws.amazon.com/states/home?region={aws_region}#/v2/executions/details/{execution_arn}"
        logging.info(f"Execution details in AWS console: {url}")

        return execution_arn
