from http import HTTPStatus


class ControllerException(Exception):
    """Base class for all thrown exceptions"""

    def __init__(self, message, status_code):
        self.message = message
        self.status_code = status_code

    def __str__(self):
        return "{} (StatusCode: {})".format(self.message, self.status_code)


class NotLoggedInException(ControllerException):
    """Thrown when auth token isn't found or is invalid."""

    def __init__(self, message: str):
        super().__init__(message, HTTPStatus.UNAUTHORIZED)


class ValidationException(ControllerException):
    """Thrown when a type error is hit when unpacking the DFT request."""

    def __init__(self, message: str):
        super().__init__(message, HTTPStatus.BAD_REQUEST)


class ClientException(Exception):
    """Thrown by the client when an API error is encountered."""

    def __init__(self, message: str):
        self.message = message

    def __str__(self) -> str:
        return f"Exception encountered during calculation: {self.message}"
