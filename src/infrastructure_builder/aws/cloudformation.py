import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import cached_property
from time import sleep
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from infrastructure_builder.aws.service_base import ServiceBase
from infrastructure_builder.exceptions import BuilderError


logger = logging.getLogger(__name__)


@dataclass
class Stack:
    name: str
    output: dict


class CloudFormation(ServiceBase):
    """
    Helper functions for AWS CloudFormation
    """
    _wait_timeout: int
    _time_between_checks: int
    _role_arn: str
    _stack_outputs = {}

    COMPLETED_STATES = [
        "CREATE_COMPLETE",
        "DELETE_COMPLETE",
        "UPDATE_COMPLETE"
    ]
    IN_PROGRESS_STATES = [
        "CREATE_IN_PROGRESS",
        "DELETE_IN_PROGRESS",
        "REVIEW_IN_PROGRESS",
        "ROLLBACK_IN_PROGRESS",
        "UPDATE_COMPLETE_CLEANUP_IN_PROGRESS",
        "UPDATE_IN_PROGRESS",
        "UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS",
        "UPDATE_ROLLBACK_IN_PROGRESS"
    ]
    FAILED_STATES = [
        "ROLLBACK_COMPLETE",
        "UPDATE_ROLLBACK_COMPLETE",
        "CREATE_FAILED",
        "DELETE_FAILED",
        "ROLLBACK_FAILED",
        "UPDATE_ROLLBACK_FAILED"
    ]

    def __init__(self, session: boto3.Session = None, region: str = None,
                 wait_timeout: int = 15, time_between_checks: int = 5,
                 role_arn: str = None):
        """
        Initializes a new helper object.

        :param session: The AWS session to use, or None to create a new one
        :param region: The region to use, or None to use the default region or the session's region
        :param wait_timeout: The timeout in minutes
        :param time_between_checks: The time to wait before checking the stack status again
        :param role_arn: The ARN of the role which CloudFormation should assume (optional)
        """
        super().__init__(session, region)
        self._wait_timeout = wait_timeout
        self._time_between_checks = time_between_checks
        self._role_arn = role_arn

    @cached_property
    def client(self):
        """
        Returns a Boto3 client for AWS CloudFormation. The client object is cached.
        :return: A Boto3 client for AWS CloudFormation
        """
        return self.session.client("cloudformation", region_name=self.region)

    def _describe_stack(self, stack_name: str):
        try:
            response = self.client.describe_stacks(StackName=stack_name)
            stacks = response["Stacks"]
            return stacks[0]
        except ClientError as err:
            if err.response["ResponseMetadata"]["HTTPStatusCode"] == 400:
                return None
            raise

    def describe_stack(self, stack_name: str) -> Optional[Stack]:
        """
        Returns information about a CloudFormation stack.

        :param stack_name: The name of the CloudFormation stack.
        :return: A Stack object, or None if the stack was not found.
        """
        stack = self._describe_stack(stack_name)
        if stack is None:
            return None

        return self._stack_outputs_to_stack(stack)

    def _delete_resource_content(self, stack_name: str):
        resources = self.client.list_stack_resources(StackName=stack_name)
        for summary in resources["StackResourceSummaries"]:
            resource_type = summary["ResourceType"]
            resource_id = summary["PhysicalResourceId"]
            if resource_type == "AWS::ECR::Repository":
                self._empty_ecr_repository(resource_id)
            elif resource_type == "AWS::S3::Bucket":
                self._empty_s3_bucket(resource_id)

    def _empty_ecr_repository(self, resource_id: str):
        logger.info(f'Deleting all images in {resource_id}')
        ecr_client = self.session.client("ecr", region_name=self.region)
        images = ecr_client.list_images(repositoryName=resource_id)
        # The response contains the first 100 images only.
        # In most cases, a repository contains a few images only, so this approach is fine.
        image_digests = [image["imageDigest"] for image in images["imageIds"]]
        if not image_digests:
            return

        resp = ecr_client.batch_delete_image(repositoryName=resource_id,
                                             imageIds=[{"imageDigest": image_digest} for image_digest in image_digests])
        failures = resp["failures"]
        if failures:
            raise BuilderError(f'Cannot empty ECR {resource_id} ({failures})')

    def _empty_s3_bucket(self, resource_id: str):
        logger.info(f'Deleting all files in {resource_id}')
        s3_client = self.session.client("s3", region_name=self.region)
        resp = s3_client.list_object_versions(Bucket=resource_id)
        # The response contains the first 1000 images only.
        # In most cases, a bucket contains a few files only, so this approach is fine.
        objects_to_delete = [{"Key": version["Key"], "VersionId": version["VersionId"]}
                             for version in resp.get("Versions", [])]
        if not objects_to_delete:
            return

        resp = s3_client.delete_objects(Bucket=resource_id, Delete={
            "Objects": objects_to_delete,
            "Quiet": True
        })
        errors = resp.get("Errors", [])
        if errors:
            raise BuilderError(f'Cannot empty S3 bucket {resource_id} ({errors})')

    def delete_stack(self, stack_name: str, delete_content: bool = False) -> None:
        """
        Delete a CloudFormation stack and optionally deletes all data which is stored in its resources.
        Data in S3 buckets and ECR registries only will be deleted.

        :param stack_name: The name of the CloudFormation stack.
        :param delete_content: If True, data in S3 buckets and ECR registries will be deleted, else no data will be
                               deleted (and the stack deletion will fail unless the resources do not have any data).
        """
        stack = self._describe_stack(stack_name)
        if stack is None:
            raise BuilderError(f"Stack {stack_name} does not exist")

        if delete_content:
            self._delete_resource_content(stack_name)

        args = dict(StackName=stack_name)
        if self._role_arn is not None:
            args["RoleARN"] = self._role_arn

        self.client.delete_stack(**args)
        self._wait_until_completed(stack["StackId"])

    def _stack_outputs_to_stack(self, stack):
        outputs = {}
        if "Outputs" in stack:
            outputs = {output_data["OutputKey"]: output_data["OutputValue"] for output_data in stack["Outputs"]}
        return Stack(stack["StackName"], outputs)

    def _wait_until_completed(self, stack_id: str) -> Stack:
        start = datetime.now(timezone.utc) - timedelta(seconds=30)
        end = start + timedelta(minutes=self._wait_timeout)
        processed_events = set()

        def print_events(all_events):
            unprocessed_events = list(filter(
                lambda e: e["Timestamp"] >= start and e["EventId"] not in processed_events, all_events))
            for event in reversed(unprocessed_events):
                logger.info((f'{event["Timestamp"]} {event["ResourceStatus"]} {event["ResourceType"]}: '
                             f'{event["LogicalResourceId"]} {event.get("ResourceStatusReason", "")}'))
                processed_events.add(event["EventId"])

        while True:
            if datetime.now(timezone.utc) > end:
                raise BuilderError("Timeout")

            stack = self._describe_stack(stack_id)
            stack_status = stack["StackStatus"]

            events = self.client.describe_stack_events(StackName=stack_id)
            print_events(events["StackEvents"])

            if stack_status in self.COMPLETED_STATES:
                break
            elif stack_status in self.IN_PROGRESS_STATES:
                # Continue loop
                pass
            elif stack_status in self.FAILED_STATES:
                raise BuilderError(f'Stack {stack["StackName"]} failed: {stack["StackStatus"]}')
            else:
                raise BuilderError(f'Stack {stack["StackName"]} entered unknown state: {stack["StackStatus"]}')

            sleep(self._time_between_checks)

        return self._stack_outputs_to_stack(stack)

    def _create_stack(self, stack_name: str, template: str, parameters: list[dict[str, str]],
                      tags: list[dict[str, str]], capabilities: list[str]) -> Stack:
        args = dict(
            StackName=stack_name,
            TemplateBody=template,
            Parameters=parameters,
            Tags=tags,
            Capabilities=capabilities
        )
        if self._role_arn is not None:
            args["RoleARN"] = self._role_arn

        stack = self.client.create_stack(**args)
        stack_id = stack["StackId"]
        logger.info(f'Stack {stack_id} created')
        return self._wait_until_completed(stack_id)

    def _update_stack(self, stack, template: str, parameters: list[dict[str, str]], tags: list[dict[str, str]],
                      capabilities: list[str]) -> Stack:
        args = dict(
            StackName=stack["StackName"],
            TemplateBody=template,
            Parameters=parameters,
            Tags=tags,
            Capabilities=capabilities
        )
        if self._role_arn is not None:
            args["RoleARN"] = self._role_arn

        try:
            updated_stack = self.client.update_stack(**args)
            stack_id = updated_stack["StackId"]
            return self._wait_until_completed(stack_id)
        except ClientError as err:
            if err.response["Error"]["Message"] == "No updates are to be performed.":
                return self._stack_outputs_to_stack(stack)
            raise

    def create_or_update_stack(self, stack_name: str,
                               template_filename: str,
                               tags: dict[str, str] = None,
                               capability_iam: bool = False,
                               capability_named_iam: bool = False,
                               capability_auto_expand: bool = False,
                               **parameters) -> Stack:
        """
        Create or update a CloudFormation stack.

        :param stack_name: The name of the CloudFormation stack.
        :param template_filename: The filename of the CloudFormation template. Both YAML and JSON are supported.
        :param tags: The tags the stack should get, a Dictionary with tag name as key and its value.
        :param capability_iam: If True, CAPABILITY_IAM will be passed to CloudFormation.
        :param capability_named_iam: If True, CAPABILITY_NAMED_IAM will be passed to CloudFormation.
        :param capability_auto_expand: If True, CAPABILITY_AUTO_EXPAND will be passed to CloudFormation.
        :param parameters: The parameters which will be passed along with the template; the keys must match the
                           parameters in the template, the value will be converted into a string.
        :return:
        """
        if tags is None:
            tags = {}

        with open(template_filename) as template_file:
            template = template_file.read()
        stack_parameters = [{"ParameterKey": key, "ParameterValue": str(value)} for key, value in parameters.items()]
        stack_tags = [{"Key": key, "Value": str(value)} for key, value in tags.items()]
        capabilities = []
        if capability_iam:
            capabilities.append("CAPABILITY_IAM")
        if capability_named_iam:
            capabilities.append("CAPABILITY_NAMED_IAM")
        if capability_auto_expand:
            capabilities.append("CAPABILITY_AUTO_EXPAND")

        stack = self._describe_stack(stack_name)
        if stack is None:
            return self._create_stack(stack_name, template, stack_parameters, stack_tags, capabilities)
        elif stack["StackStatus"] == "DELETE_COMPLETE":
            self.delete_stack(stack_name)
            return self._create_stack(stack_name, template, stack_parameters, stack_tags, capabilities)
        else:
            return self._update_stack(stack, template, stack_parameters, stack_tags, capabilities)
