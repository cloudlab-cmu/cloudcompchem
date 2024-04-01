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
    yield {
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
    assert isinstance(response.json, dict)
    e = response.json.get("energy")
    assert isinstance(e, float)
    assert e > -77 and e < -76


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
