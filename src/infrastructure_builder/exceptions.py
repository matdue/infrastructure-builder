class BuilderError(Exception):
    """
    Base exception class which represents an error while building the infrastructure.
    """
    def __init__(self, message: str):
        super().__init__(message)
