from functools import cached_property

import boto3

from infrastructure_builder.aws.service_base import ServiceBase


class Cognito(ServiceBase):
    """
    Helper functions for Amazon Cognito
    """
    def __init__(self, session: boto3.Session = None, region: str = None):
        super().__init__(session, region)

    @cached_property
    def client_idp(self):
        """
        Returns a Boto3 client for Amazon Cognito. The client object is cached.
        :return: A Boto3 client for Amazon Cognito
        """
        return self.session.client("cognito-idp", region_name=self.region)

    def get_user_pool_domain(self, domain: str) -> dict:
        """
        Returns information about the user pool domain. It contains the ARN of the CloudFront distribution and other
        details.

        :param domain: The domain string, either fully-qualified or the prefix.
        :return: A domain description object
        """
        resp = self.client_idp.describe_user_pool_domain(Domain=domain)
        return resp["DomainDescription"]
