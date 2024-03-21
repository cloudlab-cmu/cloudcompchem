from http import HTTPStatus
import logging
from dataclasses import asdict
from pysll import Constellation
from pyscf import gto, dft
from .models import DFTRequest, SinglePointEnergyResponse
from .exceptions import NotLoggedInException, DFTRequestValidationException

from flask import jsonify, make_response
from flask import request as global_request

# TODO: import exceptions up here to be used
# from exceptions import ControllerException


class DFTController:
    """This is the heart of the service which handles any training or simulation requests.

    Feel free to update this class to hold any state required for your models."""

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

    ###################################################################################
    ### You must implement the two functions below to have a functional simulation ####
    ###################################################################################

    def _run_dft_calculation(self, dft_input: DFTRequest) -> SinglePointEnergyResponse:
        """Method to run a dft calculation on the initial request payload."""
        self._logger.info("Starting dft calculation!")

        # Hopefully your model is more sophisticated!
        # build the input structure with gto
        mol = gto.M(
            atom=str(dft_input.molecule),
            basis=dft_input.basis_set,
            charge=dft_input.charge,
            spin=dft_input.spin_multiplicity,
        )
        # run the dft calculation for the given functional
        if dft_input.spin_multiplicity > 1:
            # use unrestricted kohn-sham
            calc = dft.uks(mol)
        else:
            calc = dft.rks(mol)
        calc.xc = dft_input.functional
        energy = calc.kernel()
        self._logger.info("Finished dft calculation!")

        return SinglePointEnergyResponse(energy=energy)

    def health_check(self):
        """This is used to test if the service is healthy and running.

        Generally there should be no reason to update this function."""

        return jsonify({"message": "OK"})

    def simulate_energy(self):
        """This is called when a simulation is requested.

        This should be used to (asyncronously) trigger a a run of the model.
        """

        self._logger.info("Received request to simulate a protocol!")

        # Parse the request
        try:
            dft_input = self._parse_dft_request(global_request)
        except DFTRequestValidationException as te:
            return (te.message, te.status_code)
        except NotLoggedInException as ex:
            return (ex.message, ex.status_code)
        except:
            # unhandled exception!!! return a 500
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
        response = self._run_dft_calculation(dft_input)

        # Return a 202 accepted
        return make_response(asdict(response), HTTPStatus.OK)

    def _parse_dft_request(self, request) -> DFTRequest:
        """Parse the simulation request into the auth token, the protocols to simulation, and the model to use.

        Generally there should be no reason to update this function."""
        token = self._retrieve_auth_token_from_request(request)
        try:
            self._constellation._auth_token = token
            self._constellation.me()
        except:
            raise NotLoggedInException("No authentication from login was provided!")

        # unpack the request into a struct
        req_info = request.json
        if req_info is None:
            raise DFTRequestValidationException(
                "No JSON body found, please include one to run a calculation."
            )
        dft_input = DFTRequest.from_dict(req_info)

        return dft_input
