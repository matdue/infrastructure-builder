from functools import cached_property

import boto3

from infrastructure_builder.aws.service_base import ServiceBase


class CodeArtifact(ServiceBase):
    def __init__(self, session: boto3.Session = None, region: str = None):
        super().__init__(session, region)

    @cached_property
    def client(self):
        return self.session.client("codeartifact", region_name=self.region)

    def get_authorization_token(self, domain: str, domain_owner: str, repository: str):
        token = self.client.get_authorization_token(domain=domain, domainOwner=domain_owner, durationSeconds=43200)
        repo_endpoint = self.client.get_repository_endpoint(domain=domain, domainOwner=domain_owner,
                                                            repository=repository, format="pypi")
        return dict(authorizationToken=token["authorizationToken"],
                    repositoryEndpoint=repo_endpoint["repositoryEndpoint"])
