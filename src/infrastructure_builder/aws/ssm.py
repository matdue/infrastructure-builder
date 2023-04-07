from functools import cached_property

import boto3

from infrastructure_builder.aws.service_base import ServiceBase


class SystemsManager(ServiceBase):
    """
    Helper functions for AWS Systems Manager
    """
    def __init__(self, session: boto3.Session = None, region: str = None):
        super().__init__(session, region)

    @cached_property
    def client(self):
        """
        Returns a Boto3 client for AWS Systems Manager. The client object is cached.
        :return: A Boto3 client for AWS Systems Manager
        """
        return self.session.client("ssm", region_name=self.region)

    def get_secure_string(self, parameter_name: str) -> str:
        """
        Reads a parameter from AWS Systems Manager and decodes it.

        :param parameter_name: The parameter name.
        :return: The decoded value.
        """
        resp = self.client.get_parameter(Name=parameter_name, WithDecryption=True)
        return resp["Parameter"]["Value"]

    def put_secure_string(self, parameter_name: str, parameter_value: str, overwrite: bool = False,
                          tags: dict = None, key_id: str = None) -> None:
        """
        Stores or updates a parameter in AWS Systems Manager as a secure string.

        :param parameter_name: The parameter name.
        :param parameter_value: The value to store.
        :param overwrite: If True, an already existing parameter will be overwritten, else this call will be ignored
        and the existing parameter won't get modified.
        :param tags: The tags to set with the parameter.
        :param key_id: The Key Management Service (KMS) ID that you want to use to encrypt the parameter.
        """
        if tags is None:
            tags = {}
        parameter_tags = [{"Key": key, "Value": str(value)} for key, value in tags.items()]

        args = dict(Name=parameter_name, Value=parameter_value, Type="SecureString", Overwrite=overwrite,
                    Tags=parameter_tags)
        if key_id is not None:
            args["KeyId"] = key_id
        try:
            self.client.put_parameter(**args)
        except self.client.exceptions.ParameterAlreadyExists:
            # Do not report an already existing parameter as error
            # because this task should create or update a parameter,
            # and if it exists already, this task has been fulfilled.
            pass

    def delete_secure_string(self, parameter_name: str) -> None:
        """
        Delete a parameter from AWS Systems Manager.

        :param parameter_name: The parameter name.
        """
        self.client.delete_parameter(Name=parameter_name)
