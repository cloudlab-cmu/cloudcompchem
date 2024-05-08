from math import isclose

import numpy as np
import pytest

from cloudcompchem.models import Atom, DFTOptRequest, Molecule
from cloudcompchem.opt import run_dft_opt


@pytest.fixture(scope="function")
def calc_distance_matrix(coords: np.ndarray) -> np.ndarray:
    n = len(coords)
    matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            v = coords[i] - coords[j]
            distance = np.sqrt((v * v).sum())
            matrix[i][j] = matrix[j][i] = distance
    return matrix


water_dict = {
    "atoms": [
        {"symbol": "O", "position": [0, 0, 0]},
        {"symbol": "H", "position": [0, 1, 0]},
        {"symbol": "H", "position": [0, 0, 1]},
    ],
    "charge": 0,
    "spin_multiplicity": 1,
}
water_input_dict = {
    "molecule": water_dict.copy(),
    "config": {"functional": "'b3lyp'", "basis_set": "ccpvdz"},
    "solver": "geomeTRIC",
}


@pytest.fixture(scope="function")
def water_expected_response():
    return {
        "converged": True,
        "energy": -76.471217696,
        "orbitals": [
            {"energy": -19.171027052211535, "occupancy": 2.0},
            {"energy": -0.9909480669966213, "occupancy": 2.0},
            {"energy": -0.47266274771354133, "occupancy": 2.0},
            {"energy": -0.3917614837228546, "occupancy": 2.0},
            {"energy": -0.2894290750128778, "occupancy": 2.0},
            {"energy": 0.03804360154196448, "occupancy": 0.0},
            {"energy": 0.11588306314232323, "occupancy": 0.0},
            {"energy": 0.5065491242360264, "occupancy": 0.0},
            {"energy": 0.618809332019355, "occupancy": 0.0},
            {"energy": 0.9129455648075336, "occupancy": 0.0},
            {"energy": 0.930612531542112, "occupancy": 0.0},
            {"energy": 1.0052452617860932, "occupancy": 0.0},
            {"energy": 1.0761800070059897, "occupancy": 0.0},
            {"energy": 1.2759217403838836, "occupancy": 0.0},
            {"energy": 1.342250293269888, "occupancy": 0.0},
            {"energy": 1.575434743289961, "occupancy": 0.0},
            {"energy": 1.7015414134666735, "occupancy": 0.0},
            {"energy": 2.0398134470816798, "occupancy": 0.0},
            {"energy": 2.084252729637172, "occupancy": 0.0},
            {"energy": 2.8804846548812506, "occupancy": 0.0},
            {"energy": 2.940459073742362, "occupancy": 0.0},
            {"energy": 3.031265809644373, "occupancy": 0.0},
            {"energy": 3.408867404807953, "occupancy": 0.0},
            {"energy": 3.739660908087108, "occupancy": 0.0},
        ],
        "distance_matrix": np.array(
            [[0.0, 1.83048552, 1.83048552], [1.83048552, 0.0, 2.85977529], [1.83048552, 2.85977529, 0.0]]
        ),
    }


def test_water():
    request = DFTOptRequest.from_dict(water_input_dict)
    response = run_dft_opt(request)
    expected_response = water_expected_response()
    assert response.converged
    assert isclose(response.energy, expected_response["energy"])
    assert all(
        isclose(ex_orb["energy"], t_orb.energy)
        for ex_orb, t_orb in zip(expected_response["orbitals"], response.orbitals)
    )

    coords = np.array([atom.position for atom in response.molecule.atoms])
    matrix = calc_distance_matrix(coords=coords)
    assert np.allclose(expected_response["distance_matrix"], matrix)
