from __future__ import annotations

import functools
import logging
from dataclasses import asdict

import requests
from pysll import Constellation

from cloudcompchem.dft import calculate_energy
from cloudcompchem.exceptions import NotLoggedInException, ServerException
from cloudcompchem.models import (
    EnergyRequest,
    FunctionalConfig,
    Molecule,
    SinglePointEnergyResponse,
)

logger = logging.getLogger(__file__)


# define a decorator requiring login for method
def requires_login(fn):
    @functools.wraps(fn)
    def wrapper(self: Client, *args, **kwargs):
        try:
            logger.debug("attempting to login")
            res = self._constellation.me()
            logger.debug(f"login result: {res}")
        except Exception as ex:
            logger.debug(f"hit exception: {ex}")
            raise NotLoggedInException(
                "You are not logged in! Please call client.login(username, password) before using other methods."
            )
        return fn(self, *args, **kwargs)

    return wrapper


class Client:
    def __init__(self, local: bool, constellation: Constellation = Constellation(), url: str = "http://localhost:5000"):
        self._auth_token = None
        self._url = url
        self._constellation = constellation
        self.local = local

    def login(self, username: str, password: str):
        self._constellation.login(username=username, password=password)
        self._auth_token = self._constellation._auth_token

    @requires_login
    def single_point_energy(self, molecule: Molecule, config: FunctionalConfig) -> SinglePointEnergyResponse:
        """Calculate the energy of the given molecule. The calculator does not
        need to be installed locally since the calculation is offloaded to the
        API.

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
        req = EnergyRequest(molecule=molecule, config=config)
        if self.local is True:
            return calculate_energy(req)
        else:
            return self._calculate_energy_from_url(req)

    def _calculate_energy_from_url(self, req: EnergyRequest) -> SinglePointEnergyResponse:
        # serialize the request into a dict and send the request
        req_dict = asdict(req)
        headers = {"Authorization": "Bearer " + (self._auth_token or "")}
        resp = requests.post(url=self._url + "/energy", json=req_dict, headers=headers)
        # check if the status code is 2XX, if it's not error out early
        if resp.status_code // 100 != 2:
            raise ServerException(resp.text)

        # else we populate the energy calculation object with response
        e_resp = resp.json()
        return SinglePointEnergyResponse.from_dict(e_resp)
