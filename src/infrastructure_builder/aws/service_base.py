import boto3


class ServiceBase:
    """
    Base class for any service
    """
    _region: str
    _session: boto3.Session

    def __init__(self, session: boto3.Session = None, region: str = None):
        """
        Initializes a new instances.

        :param session: The AWS session to use, or None to create a new one
        :param region: The region to use, or None to use the default region or the session's region
        """
        self._region = region
        self._session = boto3.Session(region_name=region) if session is None else session

    @property
    def region(self) -> str:
        """
        Returns the region to use, or None to use the session's region
        :return: The region or None
        """
        return self._region

    @property
    def session(self) -> boto3.Session:
        """
        Returns the AWS session
        :return: The session
        """
        return self._session
