import logging

import pytest

from cloudcompchem.models import SinglePointEnergyResponse


@pytest.fixture()
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


def test_health_check(client):
    response = client.get("/health-check")
    assert response.json == {"message": "OK"}


def test_simulate_energy(client, req_dict, caplog, match_mol, expected_energy_response):

    caplog.set_level(logging.DEBUG)
    response = client.post(
        "/energy",
        json=req_dict,
        headers={"Authorization": "Bearer abc123"},
    )
    assert response.status_code == 200
    resp = SinglePointEnergyResponse.from_dict(response.json)
    match_mol(resp, expected_energy_response)


def test_simulate_energy_spin_error(client, req_dict, caplog):
    caplog.set_level(logging.DEBUG)
    req_dict["molecule"]["spin_multiplicity"] = 0
    response = client.post(
        "/energy",
        json=req_dict,
        headers={"Authorization": "Bearer abc123"},
    )
    assert response.status_code == 400
    assert "10 and spin -1" in str(response.data)


def test_simulate_energy_charge_format_error(client, req_dict):
    req_dict["molecule"]["charge"] = "cat"
    response = client.post(
        "/energy",
        json=req_dict,
        headers={"Authorization": "Bearer abc123"},
    )
    assert response.status_code == 400
    assert "must be an integer" in str(response.data)


def test_simulate_energy_charge_value_error(client, req_dict, caplog):
    caplog.set_level(logging.DEBUG)
    req_dict["molecule"]["charge"] = 1000
    response = client.post(
        "/energy",
        json=req_dict,
        headers={"Authorization": "Bearer abc123"},
    )
    assert response.status_code == 400
    assert "invalid charge" in str(response.data)


def test_simulate_energy_basis_error(client, req_dict):
    req_dict["config"]["basis_set"] = "cat"
    response = client.post(
        "/energy",
        json=req_dict,
        headers={"Authorization": "Bearer abc123"},
    )
    assert response.status_code == 400


def test_simulate_energy_functional_error(client, req_dict, caplog):

    caplog.set_level(logging.DEBUG)
    req_dict["config"]["functional"] = "cat"
    response = client.post(
        "/energy",
        json=req_dict,
        headers={"Authorization": "Bearer abc123"},
    )
    assert response.status_code == 400
    assert "LibXCFunctional: name" in str(response.data)
