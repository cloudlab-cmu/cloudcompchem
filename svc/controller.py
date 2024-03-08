from http import HTTPStatus
import threading
import time

from flask import jsonify, make_response
from flask import request as global_request

# TODO: import exceptions up here to be used
# from exceptions import ControllerException


class DFTController:
    """This is the heart of the service which handles any training or simulation requests.

    Feel free to update this class to hold any state required for your models."""

    def __init__(self, logger, constellation):
        ###################################################################################
        ### You must update the below two varaibles based on what simulations and      ####
        ### protocols you support                                                      ####
        ###################################################################################

        # The list of simulation ids this instance of tachyon supports
        self._supported_simulation_ids = ["id:simulation"]

        # The list of protocol types that this instance of tachyon supports
        self._supported_protocol_types = ["Object.Protocol.TestProtocol"]

        ###################################################################################
        ### You generally should not need to update the below variables (but are       ####
        ### welcome to if necessary)                                                   ####
        ###################################################################################

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

    def _run_dft_calculation(self, auth_token, model_to_train, updated_datasets):
        """Called asynchronously to update your model when there's new data.

        You should update this function to do whatever logic is required to update the model.

        You may use self._constellation and the supplied auth token to download any needed information.
        """
        self._logger.info(
            "Starting fake dft calculation - you should definitely update the _run_dft_calculation method in controller.py!"
        )

        # Hopefully your model is more sophisticated!
        time.sleep(1)

        # Make sure to remove the current thread from the list of outstanding requests so we don't think its stuck
        self._in_progress_training_threads.remove(threading.current_thread())
        self._logger.info(
            "Finished fake dft calculation - you should definitely update the _run_dft_calculation method in controller.py!"
        )

    ###################################################################################
    ### You generally should not need to update the following functions, but are   ####
    ### free to do so if needed or if you're interested in how they work           ####
    ###################################################################################

    def health_check(self):
        """This is used to test if the service is healthy and running.

        Generally there should be no reason to update this function."""

        return jsonify({"message": "OK"})

    def shutdown(self):
        """This is used to shutdown the service, allowing any in progress jobs to finish within the timeout.

        Generally there should be no reason to update this function."""
        self._logger.info("Shutting down...")
        start_time = time.time()
        while (
            len(self._in_progress_training_threads)
            + len(self._in_progress_simulation_threads)
            > 0
        ):
            remaining_threads = len(self._in_progress_training_threads) + len(
                self._in_progress_simulation_threads
            )
            self._logger.info(
                "Have {} threads still running...".format(remaining_threads)
            )
            if time.time() - start_time > self._shutdown_timeout:
                self._logger.info(
                    "Exiting even though {} threads have not completed".format(
                        remaining_threads
                    )
                )
                return jsonify(
                    {
                        "message": "exited with {} threads remaining".format(
                            remaining_threads
                        )
                    }
                )
            self._logger.info("Waiting 1 second...")
            time.sleep(1)

        return jsonify({"message": "OK"})

    def simulate(self):
        """This is called when a simulation is requested.

        This should be used to (asyncronously) trigger a a run of the model.

        Generally there should be no reason to update this function."""

        self._logger.info("Received request to simulate a protocol!")

        # Parse the request
        (
            auth_token,
            dft_input,
        ) = self._parse_simulation_request(global_request)

        # Download the needed information about each object - this will also make
        # sure the request is properly formatted and contains information we have
        # permission to see
        self._logger.info(f"Received request to run DFT using: {dft_input}.")

        # validate the input
        self._logger.info(
            f"Validating input {dft_input} is suitable for simulation..."
        )

        try:
            # TODO: someone has to make this function
            validate_dft_input(dft_input)
        # NOTE: need to include several exceptions here to branch based on the
        # types of errors we expect to see
        # TODO: someone has to make new exception classes to take care of the handling
        except Exception as exc:
            self._logger.error(f"found exception while validating: {exc}")
            return {"error": True}, HTTPStatus.INTERNAL_SERVER_ERROR

        # Trigger the simulation - we can do each one in parallel
        # NOTE: this is not actually parallel in python since python has a GIL
        # for this process, but we can handle additional IO requests
        self._logger.info("Triggering async dft simulation request")
        simulation_thread = threading.Thread(
            target=self._run_dft_calculation,
            args=(auth_token, dft_input),
            daemon=True,
        )
        self._in_progress_simulation_threads.append(simulation_thread)
        simulation_thread.start()

        # Return a 202 accepted
        return make_response({"message": "OK"}, HTTPStatus.ACCEPTED)

    def _parse_simulation_request(self, request):
        """Parse the simulation request into the auth token, the protocols to simulation, and the model to use.

        Generally there should be no reason to update this function."""

        return (
            self._retrieve_auth_token_from_request(request),
            self._retrieve_data_from_request(request, "inputs"),
        )

    def _retrieve_data_from_request(self, request, field_name, required=True):
        """Retrieve data from the request with the given field name

        If required is set to true, raise an exception if the field
        does not exist in the request payload
        """
        field_value = None
        field_json = request.json
        if field_json and field_name in field_json:
            field_value = field_json[field_name]
        if required and field_value is None:
            raise MissingRequiredFieldException(field_name)
        return field_value

    def _retrieve_auth_token_from_request(self, request):
        auth_header = request.headers.get("Authorization")
        if auth_header:
            return auth_header.replace("Bearer ", "")
        return None
