import requests
import functools
from pysll import Constellation
from dataclasses import asdict
from cloudcompchem.models import (
    Molecule,
    EnergyCalculation,
    DFTRequest,
    Calculator,
    SinglePointEnergyResponse,
)
from cloudcompchem.calculators import Calculator
from cloudcompchem.exceptions import NotLoggedInException


# define a decorator requiring login for method
def requires_login(fn):
    @functools.wraps(fn)
    def wrapper(self: Client, *args, **kwargs):
        if self._auth_token is None:
            raise NotLoggedInException(
                "You are not logged in! Please call client.login(username, password) before using other methods."
            )
        else:
            fn(self, *args, **kwargs)

    return wrapper


class Client:
    def __init__(self, url="http://localhost:5000"):
        self._auth_token = None
        self._url = url
        self._constellation = Constellation()

    def login(self, username: str, password: str):
        self._constellation.login(username=username, password=password)
        self._auth_token = self._constellation._auth_token

    @requires_login
    def single_point_energy(
        self, molecule: Molecule, calculator: Calculator
    ) -> EnergyCalculation:
        """Calculate the energy of the given molecule. The calculator does not need
        to be installed locally since the calculation is offloaded to the API.

        Parameters:
        -----------
        molecule (Molecule): The chemical that will have its energy calculated.
        calculator (Calculator): The electronic structure method (with parameters)
            that calculates the energy

        Returns:
        --------
        EnergyCalculation: object that contains the results of the energy calculation
            including total energy, orbital energies, and occupancies.
        """

        # build the api request payload
        req = DFTRequest(molecule=molecule, calculator=calculator)

        # serialize the request into a dict and send the request
        req_dict = asdict(req)
        headers = {"Authorization": "Bearer " + self._auth_token}
        resp = requests.post(url=self._url + "/energy", json=req_dict, headers=headers)
        # check if the status code is 2XX, if it's not error out early
        if resp.status_code // 100 != 2:
            raise ClientException(resp.text)

        # else we populate the energy calculation object with response
        resp_obj = SinglePointEnergyResponse(**resp.json())
        return EnergyCalculation(resp_obj)
