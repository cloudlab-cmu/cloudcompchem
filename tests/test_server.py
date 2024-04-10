from unittest.mock import patch

import pytest
from pysll import Constellation

from cloudcompchem.server import create_app


@pytest.fixture()
def app():
    with patch("pysll.Constellation.me", return_value=None):
        app = create_app(constellation=Constellation())
        app.config["TESTING"] = True

        yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def req_dict():
    return {
        "functional": "pbe,pbe",
        "basis_set": "ccpvdz",
        "charge": 0,
        "spin_multiplicity": 1,
        "molecule": {
            "atoms": [
                {"symbol": "O", "position": [0, 0, 0]},
                {"symbol": "H", "position": [0, 1, 0]},
                {"symbol": "H", "position": [0, 0, 1]},
            ]
        },
    }


def test_health_check(client):
    response = client.get("/health-check")
    assert response.json == {"message": "OK"}


def test_simulate_energy(client, req_dict):
    response = client.post(
        "/energy",
        json=req_dict,
        headers={"Authorization": "Bearer abc123"},
    )
    assert response.status_code == 200
    assert response.json == {
        "energy": {
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
    }


def test_simulate_energy_spin_error(client, req_dict):
    response = client.post(
        "/energy",
        json=req_dict | {"spin_multiplicity": 0},
        headers={"Authorization": "Bearer abc123"},
    )
    assert response.status_code == 400
    assert "10 and spin -1" in str(response.data)


def test_simulate_energy_charge_format_error(client, req_dict):
    response = client.post(
        "/energy",
        json=req_dict | {"charge": "cat"},
        headers={"Authorization": "Bearer abc123"},
    )
    assert response.status_code == 400
    assert "must be an integer" in str(response.data)


def test_simulate_energy_charge_value_error(client, req_dict):
    response = client.post(
        "/energy",
        json=req_dict | {"charge": 1000},
        headers={"Authorization": "Bearer abc123"},
    )
    assert response.status_code == 400
    assert "invalid charge" in str(response.data)


def test_simulate_energy_basis_error(client, req_dict):
    response = client.post(
        "/energy",
        json=req_dict | {"basis_set": "cat"},
        headers={"Authorization": "Bearer abc123"},
    )
    assert response.status_code == 400


def test_simulate_energy_functional_error(client, req_dict):

    response = client.post(
        "/energy",
        json=req_dict | {"functional": "cat"},
        headers={"Authorization": "Bearer abc123"},
    )
    assert response.status_code == 400
    assert "LibXCFunctional: name" in str(response.data)
