from copy import deepcopy
from dataclasses import asdict

import pytest

from cloudcompchem.exceptions import DFTRequestValidationException
from cloudcompchem.models import (
    Atom,
    EnergyRequest,
    Molecule,
    SinglePointEnergyResponse,
)


def test_atom_deserialize():
    """Test whether we can make atoms from dicts."""
    a = Atom("C", (1, 2, 3))
    assert a.symbol == "C" and a.position == (1, 2, 3)

    a = Atom(**{"symbol": "C", "position": (1, 2, 3)})
    assert a.symbol == "C" and a.position == (1, 2, 3)


def test_atom_serialize():
    """Test whether we can serialize atoms into dicts."""
    a = Atom("C", (1, 2, 3))
    assert asdict(a) == {"symbol": "C", "position": (1, 2, 3)}


def test_molecule_deserialize(req_dict):
    """Test whether we can deserialize a molecule from dicts."""
    atom_dicts = req_dict["molecule"]
    mol = Molecule.from_dict(atom_dicts)
    assert len(mol.atoms) == 3
    assert [a.symbol for a in mol.atoms] == ["O", "H", "H"]
    assert [a.position for a in mol.atoms] == [[0, 0, 0], [0, 1, 0], [0, 0, 1]]


def test_invalid_molecule_deserialization():
    """Test that we get a ValueError when trying to build a Molecule from an
    invalid dictionary."""
    with pytest.raises(ValueError):
        Molecule.from_dict(
            {
                "atomsss": [  # make a typo here
                    {"symbol": "O", "position": [0, 0, 0]},
                    {"symbol": "H", "position": [0, 1, 0]},
                    {"symbol": "H", "position": [0, 0, 1]},
                ],
                "charge": 0,
                "spin_multiplicity": 1,
            }
        )

    with pytest.raises(ValueError):
        Molecule.from_dict(
            {
                "atoms": {"symbol": "O", "position": [0, 0, 0]},  # make atoms value not a list
                "charge": 0,
                "spin_multiplicity": 1,
            }
        )


def test_molecule_serialize(mol):
    """Test whether we can serialize molecules into dicts."""
    assert asdict(mol) == {
        "atoms": [
            {"symbol": "O", "position": [0, 0, 0]},
            {"symbol": "H", "position": [0, 1, 0]},
            {"symbol": "H", "position": [0, 0, 1]},
        ],
        "charge": 0,
        "spin_multiplicity": 1,
    }


def test_molecule_to_string(mol):
    """Test whether we can serialize molecules into dicts."""
    assert str(mol) == "O 0 0 0; H 0 1 0; H 0 0 1"


def test_request_deserialization(req_dict):
    """Test whether we can deserialize entire dft request."""

    # NOTE: need to copy b/c 'from_dict' modifies the input dict inplace
    cpy = deepcopy(req_dict)
    r = EnergyRequest.from_dict(req_dict)
    assert asdict(r) == cpy


def test_invalid_request_deserialization(req_dict):
    """Test whether we can deserialize entire dft request."""
    with pytest.raises(DFTRequestValidationException):
        EnergyRequest.from_dict(req_dict | {"molecule": "blah"})

    # delete the molecules key
    req_dict.pop("molecule")
    with pytest.raises(DFTRequestValidationException):
        EnergyRequest.from_dict(req_dict)


def test_single_point_energy_deserialization(expected_energy_response):
    resp = SinglePointEnergyResponse.from_dict(expected_energy_response)
    assert asdict(resp) == expected_energy_response
