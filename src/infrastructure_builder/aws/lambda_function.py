import logging
from functools import cached_property
from time import sleep

import boto3

from infrastructure_builder.aws.service_base import ServiceBase


logger = logging.getLogger(__name__)


class LambdaFunction(ServiceBase):
    """
    Helper functions for AWS Lambda
    """
    def __init__(self, session: boto3.Session = None, region: str = None):
        super().__init__(session, region)

    @cached_property
    def client(self):
        """
        Returns a Boto3 client for AWS Lambda. The client object is cached.
        :return: A Boto3 client for AWS Lambda
        """
        return self.session.client("lambda", region_name=self.region)

    def update_function_code(self, function_name: str, image_uri: str, alias: str = None,
                             provision: int = None) -> None:
        """
        Updates the code of an AWS Lambda Function and generate a new version.

        :param function_name: The name of the Lambda Function.
        :param image_uri: The Docker Image URI with the latest code.
        :param alias: If not None, update this alias to the new version
        :param provision: If not None, provision the Lambda Function for n concurrent executions.
        """
        response = self.client.update_function_code(FunctionName=function_name, ImageUri=image_uri, Publish=True)
        if alias:
            function_version = response["Version"]
            try:
                self.client.update_alias(FunctionName=function_name, Name=alias, FunctionVersion=function_version)
            except self.client.exceptions.ResourceNotFoundException:
                self.client.create_alias(FunctionName=function_name, Name=alias, FunctionVersion=function_version)

            if provision:
                self.client.put_provisioned_concurrency_config(FunctionName=function_name,
                                                               Qualifier=alias,
                                                               ProvisionedConcurrentExecutions=provision)

            while True:
                alias_config = self.client.get_alias(FunctionName=function_name, Name=alias)
                if (alias_config["FunctionVersion"] == function_version or
                        "RoutingConfig" not in alias_config or
                        "AdditionalVersionWeights" not in alias_config["RoutingConfig"] or
                        len(alias_config["RoutingConfig"]["AdditionalVersionWeights"]) == 0):
                    break
                logger.info("Waiting for new Lambda version becoming active")
                sleep(3)

    def delete_old_versions(self, function_name: str, keep_latest_versions: int = 5) -> list[str]:
        """
        Delete old Lambda Function versions and keep the latest n only.

        :param function_name: The name of the Lambda Function.
        :param keep_latest_versions: Keep the latest n versions and delete the remaining. n must be 1 or greater.
        :return: List of versions which have been deleted
        """
        if keep_latest_versions < 1:
            raise ValueError("keep_latest_versions must be 1 or greater")

        deleted_versions = []
        paginator = self.client.get_paginator("list_versions_by_function")
        versions = [version
                    for response_page in paginator.paginate(FunctionName=function_name)
                    for version in response_page["Versions"]
                    if version["Version"] != "$LATEST"]
        versions = sorted(versions, key=lambda version: version["LastModified"], reverse=True)
        # First entry is version $LATEST which is equal to the second entry, so we have to skip one more
        #for outdated_version in versions[(keep_latest_versions+1):]:
        for outdated_version in versions[keep_latest_versions:]:
            deleted_versions.append(outdated_version["Version"])
            self.client.delete_function(FunctionName=function_name, Qualifier=outdated_version["Version"])

        return deleted_versions
