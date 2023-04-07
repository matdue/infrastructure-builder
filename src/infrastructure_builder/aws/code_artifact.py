from functools import cached_property

import boto3

from infrastructure_builder.aws.service_base import ServiceBase


class CodeArtifact(ServiceBase):
    """
    Helper functions for AWS CodeArtifact
    """
    def __init__(self, session: boto3.Session = None, region: str = None):
        super().__init__(session, region)

    @cached_property
    def client(self):
        """
        Returns a Boto3 client for AWS CodeArtifact. The client object is cached.
        :return: A Boto3 client for AWS CodeArtifact
        """
        return self.session.client("codeartifact", region_name=self.region)

    def get_authorization_token_pypi(self, domain: str, domain_owner: str, repository: str) -> dict:
        """
        Retrieves the authorization token to access AWS CodeArtifact. It returns also the endpoint for Python artifacts.
        The result is a dictionary with the following keys:

        authorizationToken: Authorization token
        repositoryEndpoint: URL of repository for Python artifacts

        :param domain: The name of the domain.
        :param domain_owner: The 12-digit account number of the account which owns the domain.
        :param repository: The name of the repository.
        :return: Dictionary with data to access code repository for Python artifacts
        """
        token = self.client.get_authorization_token(domain=domain, domainOwner=domain_owner, durationSeconds=43200)
        repo_endpoint = self.client.get_repository_endpoint(domain=domain, domainOwner=domain_owner,
                                                            repository=repository, format="pypi")
        return dict(authorizationToken=token["authorizationToken"],
                    repositoryEndpoint=repo_endpoint["repositoryEndpoint"])
