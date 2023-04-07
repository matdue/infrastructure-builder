from functools import cached_property

import boto3

from infrastructure_builder.aws.service_base import ServiceBase


class Route53(ServiceBase):
    """
    Helper functions for Amazon Route 53
    """
    def __init__(self, session: boto3.Session = None):
        super().__init__(session, "aws-global")

    @cached_property
    def client(self):
        """
        Returns a Boto3 client for Amazon Route 53. The client object is cached.
        :return: A Boto3 client for Amazon Route 53
        """
        return self.session.client("route53", region_name=self.region)

    def list_hosted_zones(self) -> list:
        """
        Returns all hosted zones.

        :return: All hosted zones
        """
        paginator = self.client.get_paginator("list_hosted_zones")
        hosted_zones = [hosted_zone
                        for response_page in paginator.paginate()
                        for hosted_zone in response_page["HostedZones"]]
        return hosted_zones
