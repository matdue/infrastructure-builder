from functools import cached_property

import boto3

from infrastructure_builder.aws.service_base import ServiceBase


class SecurityTokenService(ServiceBase):
    """
    Helper functions for AWS Security Token Service
    """
    def __init__(self, session: boto3.Session = None, region: str = None):
        super().__init__(session, region)

    @cached_property
    def client(self):
        """
        Returns a Boto3 client for AWS Security Token Service. The client object is cached.
        :return: A Boto3 client for AWS Security Token Service
        """
        return self.session.client("sts", region_name=self.region)

    def get_session_token(self) -> tuple:
        """
        Returns a set of temporary credentials for an Amazon Web Services account or IAM user.

        :return: A tuple (access key ID, secret access key, session token) representing temporary credentials
        """
        resp = self.client.get_session_token()
        return (resp["Credentials"]["AccessKeyId"],
                resp["Credentials"]["SecretAccessKey"],
                resp["Credentials"]["SessionToken"])
