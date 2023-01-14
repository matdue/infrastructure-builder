from functools import cached_property

import boto3

from infrastructure_builder.aws.service_base import ServiceBase


class SecurityTokenService(ServiceBase):
    def __init__(self, session: boto3.Session = None, region: str = None):
        super().__init__(session, region)

    @cached_property
    def client(self):
        return self.session.client("sts", region_name=self.region)

    def get_session_token(self):
        resp = self.client.get_session_token()
        return (resp["Credentials"]["AccessKeyId"],
                resp["Credentials"]["SecretAccessKey"],
                resp["Credentials"]["SessionToken"])
