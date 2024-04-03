import pytest
from .app import create_app
from pysll.models import Object
import logging


@pytest.fixture()
def app():
    app = create_app(constellation=MockConstellation())
    app.config.update({"TESTING": True})

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


def test_simulate_energy(client, req_dict, caplog):
    caplog.set_level(logging.DEBUG)
    response = client.post(
        "/energy",
        json=req_dict,
        headers={"Authorization": "Bearer abc123"},
    )
    assert response.status_code == 200
    assert isinstance(response.json, dict)

    resp_dict = response.json
    e = resp_dict.get("energy")
    assert isinstance(e, float)
    assert e > -77 and e < -76

    assert c["converged"] is True

    mo_es = resp_dict.get("orbital_energies")
    assert isinstance(mo_es, list)
    assert all(isinstance(en, float) for en in mo_es)

    mo_occ = resp_dict.get("orbital_occupancies")
    assert isinstance(mo_occ, list)
    assert all(isinstance(oc, float) for oc in mo_occ)
    assert sum(mo_occ) == 10.0


def test_simulate_energy_spin_error(client, req_dict, caplog):
    caplog.set_level(logging.DEBUG)
    req_dict["spin_multiplicity"] = 0
    response = client.post(
        "/energy",
        json=req_dict,
        headers={"Authorization": "Bearer abc123"},
    )
    assert response.status_code == 400
    assert "10 and spin -1" in str(response.data)


def test_simulate_energy_charge_format_error(client, req_dict, caplog):
    caplog.set_level(logging.DEBUG)
    req_dict["charge"] = "cat"
    response = client.post(
        "/energy",
        json=req_dict,
        headers={"Authorization": "Bearer abc123"},
    )
    assert response.status_code == 400
    assert "must be an integer" in str(response.data)


def test_simulate_energy_charge_value_error(client, req_dict, caplog):
    caplog.set_level(logging.DEBUG)
    req_dict["charge"] = 1000
    response = client.post(
        "/energy",
        json=req_dict,
        headers={"Authorization": "Bearer abc123"},
    )
    assert response.status_code == 400
    assert "invalid charge" in str(response.data)


def test_simulate_energy_basis_error(client, req_dict, caplog):
    caplog.set_level(logging.DEBUG)
    req_dict["basis_set"] = "cat"
    response = client.post(
        "/energy",
        json=req_dict,
        headers={"Authorization": "Bearer abc123"},
    )
    assert response.status_code == 400
    assert "Unknown basis format" in str(response.data)


def test_simulate_energy_functional_error(client, req_dict, caplog):
    caplog.set_level(logging.DEBUG)
    req_dict["functional"] = "cat"
    response = client.post(
        "/energy",
        json=req_dict,
        headers={"Authorization": "Bearer abc123"},
    )
    assert response.status_code == 400
    assert "LibXCFunctional: name" in str(response.data)


class MockConstellation:
    def __init__(self) -> None:
        self._auth_token = None

    def download(self, object: Object, fields: list[str]):
        mock_object = mock_objects_by_id.get(object.id, {})
        return {field: mock_object.get(field) for field in fields}

    def me(self):
        if self._auth_token != "abc123":
            raise Exception


mock_objects_by_id = {}
