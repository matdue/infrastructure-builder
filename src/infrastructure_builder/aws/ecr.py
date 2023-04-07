import base64
from functools import cached_property
from urllib.parse import urlparse

import boto3

from infrastructure_builder.aws.service_base import ServiceBase


class ElasticContainerRegistry(ServiceBase):
    """
    Helper functions for Amazon Elastic Container Registry
    """
    def __init__(self, session: boto3.Session = None, region: str = None):
        super().__init__(session, region)

    @cached_property
    def client(self):
        """
        Returns a Boto3 client for Amazon Elastic Container Registry. The client object is cached.
        :return: A Boto3 client for Amazon Elastic Container Registry
        """
        return self.session.client("ecr", region_name=self.region)

    @cached_property
    def public_client(self):
        """
        Returns a Boto3 client for Amazon ECR Public. The client object is cached.
        :return: A Boto3 client for Amazon ECR Public
        """
        return self.session.client("ecr-public", region_name="us-east-1")

    def get_authorization_token(self) -> dict:
        """
        Retrieves an authorization token for a private registry which can be used for docker login command.
        The result is a dictionary with the following keys:

        user: The username
        password: The password
        hostname: The registry URL for docker login command

        :return: Dictionary with authorization token
        """
        resp = self.client.get_authorization_token()
        auth_data = resp["authorizationData"][0]
        auth_token = base64.b64decode(auth_data["authorizationToken"]).decode("utf-8").split(":")
        hostname = urlparse(auth_data["proxyEndpoint"]).netloc
        return dict(user=auth_token[0], password=auth_token[1], hostname=hostname)

    def get_public_authorization_token(self) -> dict:
        """
        Retrieves an authorization token for a public registry which can be used for docker login command.
        The result is a dictionary with the following keys:

        user: The username
        password: The password

        :return: Dictionary with authorization token
        """
        resp = self.public_client.get_authorization_token()
        auth_data = resp["authorizationData"]
        auth_token = base64.b64decode(auth_data["authorizationToken"]).decode("utf-8").split(":")
        return dict(user=auth_token[0], password=auth_token[1])
