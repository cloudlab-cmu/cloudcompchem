from http import HTTPStatus


class ControllerException(Exception):
    """Base class for all thrown exceptions"""

    def __init__(self, message, status_code):
        self.message = message
        self.status_code = status_code

    def __str__(self):
        return "{} (StatusCode: {})".format(self.message, self.status_code)


class UnsupportedSimulationException(ControllerException):
    """Thrown when a simulation is requested that is not supported by this instance of tachyon"""

    def __init__(self, simulation_id):
        super().__init__(
            "The Simulation {} is not supported by this instance of tachyon.  Please use another Simulation and try again".format(
                simulation_id
            ),
            HTTPStatus.BAD_REQUEST,
        )


class UnsupportedProtocolTypeException(ControllerException):
    """Thrown when there is a request for a protocol type that is not supported by this instance of tachyon"""

    def __init__(self, protocol_type):
        super().__init__(
            "The Protoocl type {} is not supported by this instance of tachyon.  Please use another protocol type and try again".format(
                protocol_type
            ),
            HTTPStatus.BAD_REQUEST,
        )


class UnsupportedProtocolStatusException(ControllerException):
    """Thrown when there is a request to simulate a protocol that is not in processing state"""

    def __init__(self, protocol_id, protocol_type):
        super().__init__(
            "The Protoocl {} is in Status {}, which prevents it from being simulated.  Please use another protocol or ensure the protocol is in Processing Status and try again".format(
                protocol_id, protocol_type
            ),
            HTTPStatus.BAD_REQUEST,
        )


class MissingRequiredFieldException(ControllerException):
    """Thrown when the request is missing a required field"""

    def __init__(self, field_name):
        super().__init__(
            "The request is missing required field {}.  Please update your request and try again".format(
                field_name
            ),
            HTTPStatus.BAD_REQUEST,
        )
