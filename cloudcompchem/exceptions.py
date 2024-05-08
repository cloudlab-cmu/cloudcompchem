from http import HTTPStatus


class ServerException(Exception):
    """Base class for all exceptions thrown during server runtime, inferred
    from non 2xx responses."""

    def __init__(self, message):
        self.message = message

    def __str__(self) -> str:
        return f"Server Exception: {self.message}"


class MoleculeSpinAndChargeViolationError(Exception):
    """Triggered when the spin multiplicity and charge for a molecule are
    invalid."""

    def __init__(self, spin_multiplicity: int, charge: int):
        self.spin_multiplicity = spin_multiplicity
        self.charge = charge

    def __str__(self):
        return (
            f"Invalid molecule spin and charge multiplicity: charge = {self.charge} and spin {self.spin_multiplicity}"
        )


class ControllerException(Exception):
    """Base class for all thrown exceptions."""

    def __init__(self, message, status_code):
        self.message = message
        self.status_code = status_code

    def __str__(self):
        return f"{self.message} (StatusCode: {self.status_code})"


class NotLoggedInException(ControllerException):
    """Thrown when auth token isn't found or is invalid."""

    def __init__(self, message: str):
        super().__init__(message, HTTPStatus.UNAUTHORIZED)


class DFTRequestValidationException(ControllerException):
    """Thrown when a type error is hit when unpacking the DFT request."""

    def __init__(self, message: str):
        super().__init__(message, HTTPStatus.BAD_REQUEST)
