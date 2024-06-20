import logging
from dataclasses import asdict
from http import HTTPStatus

from flask import jsonify, make_response
from flask import request as global_request
from pysll import Constellation

from cloudcompchem.dft import calculate_energy
from cloudcompchem.exceptions import (
    DFTRequestValidationException,
    MoleculeSpinAndChargeViolationError,
    NotLoggedInException,
)
from cloudcompchem.models import EnergyRequest


class DFTController:
    """This is the heart of the service which handles any training or
    simulation requests.

    Feel free to update this class to hold any state required for your
    models.
    """

    def __init__(self, logger: logging.Logger, constellation: Constellation):

        # The logger that should be used
        self._logger = logger

        # The constellation wrapper descibes how the auth service connects to constellation
        self._constellation = constellation

        # Keep track of any in progress training requests
        self._in_progress_dft_threads = []

        # shutdown timeout - in seconds.  By default give all the worker threads
        # 10 seconds before killing them on shutdown.
        self._shutdown_timeout = 10

    """
    You must implement the two functions below to have a functional simulation
    """

    def health_check(self):
        """This is used to test if the service is healthy and running.

        Generally there should be no reason to update this function.
        """

        return jsonify({"message": "OK"})

    def simulate_energy(self):
        """This is called when a simulation is requested.

        This should be used to (asynchronously) trigger a a run of the
        model.
        """

        self._logger.info("Received request to simulate a molecule!")

        # Parse the request
        try:
            dft_input = self._parse_dft_request(global_request)
        except MoleculeSpinAndChargeViolationError as err:
            return (str(err), HTTPStatus.BAD_REQUEST)
        except DFTRequestValidationException as err:
            self._logger.error(f"Validation error: {err.message} Returning")
            return (err.message, err.status_code)
        except NotLoggedInException as err:
            self._logger.error("Not logged in! Returning")
            return (err.message, err.status_code)
        except Exception as err:
            self._logger.error(f"Unhandled exception: {err}")
            return (
                "Error encountered while unpacking request JSON, please inspect for errors and try again.",
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        # Download the needed information about each object - this will also make
        # sure the request is properly formatted and contains information we have
        # permission to see
        self._logger.info(f"Received request to run DFT using: {dft_input}.")

        # Trigger the simulation - we can do each one in parallel
        # NOTE: this is not actually parallel in python since python has a GIL
        # for this process, but we can handle additional IO requests
        self._logger.info("Triggering dft simulation request")

        try:
            energy_dict = calculate_energy(dft_input)
        except (RuntimeError, KeyError) as err:
            message = f"Runtime error encountered during DFT calculation due to misconfigured inputs: {err}"
            self._logger.warning(message)
            return message, HTTPStatus.BAD_REQUEST
        except AssertionError:
            message = "Found a runtime exception likely due to an invalid charge specification."
            self._logger.warning(message)
            return message, HTTPStatus.BAD_REQUEST
        except Exception as err:
            self._logger.error(f"Unhandled exception of type ({type(err)}): {err}.")
            return f"Unhandled exception: {err}.", HTTPStatus.INTERNAL_SERVER_ERROR

        return make_response(asdict(energy_dict), HTTPStatus.OK)

    def geom_opt(self):
        """This is called when a geometry optimization job is requested.

        This should be used to (asynchronously) trigger a a run of the
        model.
        """

        self._logger.info("Received request to optimize a molecule!")

    def _parse_dft_request(self, request) -> EnergyRequest:
        """Parse the simulation request into the auth token, the protocols to
        simulation, and the model to use.

        Generally there should be no reason to update this function.
        """
        # TODO: move this to a require_login decorator. this function should take request.json, not request.
        token = self._retrieve_auth_token_from_request(request)
        self._logger.info("Got token from request! Attempting to validate token...")
        self._constellation._auth_token = token
        try:
            _ = self._constellation.me()
        except Exception:
            raise NotLoggedInException("No authentication from login was provided!") from None
        self._logger.info("Token validated!")

        # unpack the request into a struct
        req_info = request.json
        self._logger.info("Attempting to unmarshal the request payload to internal struct...")
        self._logger.debug(f"req info = {req_info}")
        if req_info is None:
            raise DFTRequestValidationException("No JSON body found, please include one to run a calculation.")

        dft_input = EnergyRequest.from_dict(req_info)

        self._logger.info("Request constructed!")

        return dft_input

    def _retrieve_auth_token_from_request(self, request):
        auth_header = request.headers.get("Authorization")
        if auth_header:
            return auth_header.replace("Bearer ", "")
        return None
