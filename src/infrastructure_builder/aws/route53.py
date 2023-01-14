from functools import cached_property

import boto3

from infrastructure_builder.aws.service_base import ServiceBase


class Route53(ServiceBase):
    def __init__(self, session: boto3.Session = None):
        super().__init__(session, "aws-global")

    @cached_property
    def client(self):
        return self.session.client("route53", region_name=self.region)

    def list_hosted_zones(self):
        resp = self.client.list_hosted_zones(MaxItems="100")
        return resp["HostedZones"]
