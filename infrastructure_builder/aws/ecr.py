import base64
from functools import cached_property
from urllib.parse import urlparse

import boto3

from infrastructure_builder.aws.service_base import ServiceBase


class ElasticContainerRegistry(ServiceBase):
    def __init__(self, session: boto3.Session = None, region: str = None):
        super().__init__(session, region)

    @cached_property
    def client(self):
        return self.session.client("ecr", region_name=self.region)

    @cached_property
    def public_client(self):
        return self.session.client("ecr-public", region_name="us-east-1")

    def get_authorization_token(self):
        resp = self.client.get_authorization_token()
        auth_data = resp["authorizationData"][0]
        auth_token = base64.b64decode(auth_data["authorizationToken"]).decode("utf-8").split(":")
        hostname = urlparse(auth_data["proxyEndpoint"]).netloc
        return dict(user=auth_token[0], password=auth_token[1], hostname=hostname)

    def get_public_authorization_token(self):
        resp = self.public_client.get_authorization_token()
        auth_data = resp["authorizationData"]
        auth_token = base64.b64decode(auth_data["authorizationToken"]).decode("utf-8").split(":")
        return dict(user=auth_token[0], password=auth_token[1])
