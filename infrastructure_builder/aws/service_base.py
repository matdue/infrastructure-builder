import boto3


class ServiceBase:
    _region: str
    _session: boto3.Session

    def __init__(self, session: boto3.Session, region: str):
        self._region = region
        self._session = boto3.Session(region_name=region) if session is None else session

    @property
    def region(self):
        return self._region

    @property
    def session(self):
        return self._session
