import pytest
from cloudcompchem.models import Molecule, Atom, DFTRequest
from cloudcompchem.exceptions import DFTRequestValidationException
from dataclasses import asdict


@pytest.fixture()
def mol():
    atom_dicts = {
        "atoms": [
            {"symbol": "O", "position": [0, 0, 0]},
            {"symbol": "H", "position": [0, 1, 0]},
            {"symbol": "H", "position": [0, 0, 1]},
        ]
    }
    yield Molecule.from_dict(atom_dicts)


@pytest.fixture()
def req_dict():
    yield {
        "functional": "b3lyp",
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


def test_atom_deserialize():
    """Test whether we can make atoms from dicts."""
    a = Atom("C", [1, 2, 3])
    assert a.symbol == "C" and a.position == [1, 2, 3]

    a = Atom(**{"symbol": "C", "position": [1, 2, 3]})
    assert a.symbol == "C" and a.position == [1, 2, 3]


def test_atom_serialize():
    """Test whether we can serialize atoms into dicts."""
    a = Atom("C", [1, 2, 3])
    assert asdict(a) == {"symbol": "C", "position": [1, 2, 3]}


def test_molecule_deserialize():
    """Test whether we can deserialize a molecule from dicts."""
    atom_dicts = {
        "atoms": [
            {"symbol": "O", "position": [0, 0, 0]},
            {"symbol": "H", "position": [0, 1, 0]},
            {"symbol": "H", "position": [0, 0, 1]},
        ]
    }
    mol = Molecule.from_dict(atom_dicts)
    assert len(mol.atoms) == 3
    assert [a.symbol for a in mol.atoms] == ["O", "H", "H"]
    assert [a.position for a in mol.atoms] == [[0, 0, 0], [0, 1, 0], [0, 0, 1]]


def test_invalid_molecule_deserialization():
    """Test whether we can deserialize a molecule from dicts."""
    atom_dicts = {
        # make a typo here
        "atomsss": [
            {"symbol": "O", "position": [0, 0, 0]},
            {"symbol": "H", "position": [0, 1, 0]},
            {"symbol": "H", "position": [0, 0, 1]},
        ]
    }
    try:
        res = Molecule.from_dict(atom_dicts)
    except Exception as e:
        res = e
    assert isinstance(res, DFTRequestValidationException)
    assert "atoms" in res.message
    assert res.status_code == 400

    atom_dicts = {
        # make atoms value not a list
        "atoms": {"symbol": "O", "position": [0, 0, 0]}
    }
    try:
        res = Molecule.from_dict(atom_dicts)
    except Exception as e:
        res = e
    assert isinstance(res, DFTRequestValidationException)
    assert "list" in res.message
    assert res.status_code == 400


def test_molecule_serialize(mol):
    """Test whether we can serialize molecules into dicts."""
    assert asdict(mol) == {
        "atoms": [
            {"symbol": "O", "position": [0, 0, 0]},
            {"symbol": "H", "position": [0, 1, 0]},
            {"symbol": "H", "position": [0, 0, 1]},
        ]
    }


def test_molecule_to_string(mol):
    """Test whether we can serialize molecules into dicts."""
    assert str(mol) == "O 0 0 0; H 0 1 0; H 0 0 1"


def test_request_deserialization(req_dict):
    """Test whether we can deserialize entire dft request."""
    # NOTE: need to copy b/c 'from_dict' modifies the input dict inplace
    cpy = req_dict.copy()
    r = DFTRequest.from_dict(req_dict)
    assert asdict(r) == cpy


def test_invalid_request_deserialization(req_dict):
    """Test whether we can deserialize entire dft request."""
    inv_req_dict = req_dict.copy()
    # change the molecules key to something that doesn't match
    inv_req_dict["molecule"] = "blah"
    try:
        r = DFTRequest.from_dict(inv_req_dict)
    except Exception as e:
        r = e
    assert isinstance(r, DFTRequestValidationException)
    assert "JSON" in r.message
    assert r.status_code == 400

    # delete the molecules key
    del req_dict["molecule"]
    try:
        r = DFTRequest.from_dict(req_dict)
    except Exception as e:
        r = e
    assert isinstance(r, DFTRequestValidationException)
    assert "No molecule" in r.message
    assert r.status_code == 400
