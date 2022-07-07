from functools import cached_property

import boto3

from infrastructure_builder.aws.service_base import ServiceBase


class Cognito(ServiceBase):
    def __init__(self, session: boto3.Session = None, region: str = None):
        super().__init__(session, region)

    @cached_property
    def client_idp(self):
        return self.session.client("cognito-idp", region_name=self.region)

    def get_user_pool_domain(self, domain: str):
        resp = self.client_idp.describe_user_pool_domain(Domain=domain)
        return resp["DomainDescription"]
