from math import isclose
from unittest.mock import patch

import pytest
from pysll import Constellation

from cloudcompchem.client import Client
from cloudcompchem.models import Molecule, SinglePointEnergyResponse
from cloudcompchem.server import create_app


@pytest.fixture(scope="session")
def app():
    with patch("pysll.Constellation.me", return_value=None):
        app = create_app(constellation=Constellation())
        app.config["TESTING"] = True

        yield app


@pytest.fixture(scope="function")
def mol():
    atom_dicts = {
        "atoms": [
            {"symbol": "O", "position": [0, 0, 0]},
            {"symbol": "H", "position": [0, 1, 0]},
            {"symbol": "H", "position": [0, 0, 1]},
        ],
        "charge": 0,
        "spin_multiplicity": 1,
    }
    return Molecule.from_dict(atom_dicts)


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()


@pytest.fixture(scope="function")
def sdk_client(expected_energy_response):
    with patch("pysll.Constellation.me", return_value=None), patch(
        "cloudcompchem.client.Client._calculate_energy_from_url",
        return_value=SinglePointEnergyResponse.from_dict(expected_energy_response),
    ):
        c = Client(local=False, constellation=Constellation())
        yield c


@pytest.fixture(scope="function")
def local_sdk_client(expected_energy_response):
    with patch("pysll.Constellation.me", return_value=None), patch(
        "cloudcompchem.client.Client._calculate_energy_from_url",
        return_value=SinglePointEnergyResponse.from_dict(expected_energy_response),
    ):
        c = Client(local=True, constellation=Constellation())
        yield c


@pytest.fixture(scope="function")
def match_mol():
    return mol_matcher


@pytest.fixture(scope="function")
def expected_energy_response():
    return {
        "converged": True,
        "energy": -76.33031780985159,
        "orbitals": [
            {"energy": -18.752172955173354, "occupancy": 2.0},
            {"energy": -0.8981074252667383, "occupancy": 2.0},
            {"energy": -0.41827646305113936, "occupancy": 2.0},
            {"energy": -0.33244463860943163, "occupancy": 2.0},
            {"energy": -0.22606441107905723, "occupancy": 2.0},
            {"energy": 0.018896864509185606, "occupancy": 0.0},
            {"energy": 0.09474951776925271, "occupancy": 0.0},
            {"energy": 0.4686286596516729, "occupancy": 0.0},
            {"energy": 0.5732120055126462, "occupancy": 0.0},
            {"energy": 0.8637030310769265, "occupancy": 0.0},
            {"energy": 0.8825744834857628, "occupancy": 0.0},
            {"energy": 0.9581037355111632, "occupancy": 0.0},
            {"energy": 1.0270725783673582, "occupancy": 0.0},
            {"energy": 1.2209998378475277, "occupancy": 0.0},
            {"energy": 1.2892607510989995, "occupancy": 0.0},
            {"energy": 1.5192170841069328, "occupancy": 0.0},
            {"energy": 1.642925527415433, "occupancy": 0.0},
            {"energy": 1.9730348410011573, "occupancy": 0.0},
            {"energy": 2.014591748568126, "occupancy": 0.0},
            {"energy": 2.7912042390159555, "occupancy": 0.0},
            {"energy": 2.8519599289595794, "occupancy": 0.0},
            {"energy": 2.9386940388847598, "occupancy": 0.0},
            {"energy": 3.32053671239125, "occupancy": 0.0},
            {"energy": 3.646663078270252, "occupancy": 0.0},
        ],
    }


def mol_matcher(resp: SinglePointEnergyResponse, expected_response: dict):

    assert resp.converged is True
    assert isclose(resp.energy, expected_response["energy"])
    # make sure all orbital energies are close
    assert all(
        isclose(ex_orb["energy"], t_orb.energy) for ex_orb, t_orb in zip(expected_response["orbitals"], resp.orbitals)
    )
    # make sure all orbital occupancies are close
    assert all(
        isclose(ex_orb["occupancy"], t_orb.occupancy)
        for ex_orb, t_orb in zip(expected_response["orbitals"], resp.orbitals)
    )


@pytest.fixture(scope="function")
def req_dict():
    return {
        "config": {
            "functional": "pbe,pbe",
            "basis_set": "ccpvdz",
        },
        "molecule": {
            "atoms": [
                {"symbol": "O", "position": [0, 0, 0]},
                {"symbol": "H", "position": [0, 1, 0]},
                {"symbol": "H", "position": [0, 0, 1]},
            ],
            "charge": 0,
            "spin_multiplicity": 1,
        },
    }
