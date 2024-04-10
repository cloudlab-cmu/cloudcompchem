from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
from pyscf.dft import RKS, UKS

from cloudcompchem.exceptions import DFTRequestValidationException
from cloudcompchem.models import Molecule, Orbital, SinglePointEnergyResponse
from cloudcompchem.utils import M

logger = logging.getLogger("cloudcompchem.dft")


@dataclass
class EnergyRequest:
    molecule: Molecule
    functional: str
    basis_set: str
    spin_multiplicity: int
    charge: int

    @staticmethod
    def from_dict(d: dict) -> EnergyRequest:
        """Create a DFTRequest object from a json-like dictionary, which
        typically comes from a web request."""
        # unpack the nested molecule struct first
        molecule_data = d.pop("molecule")
        if not molecule_data:
            raise ValueError("No molecule information contained in request.")

        if not isinstance(d.get("charge"), int):
            raise DFTRequestValidationException("Charge must be an integer.")

        return EnergyRequest(molecule=Molecule.from_dict(molecule_data), **d)


def calculate_energy(dft_input: EnergyRequest) -> SinglePointEnergyResponse:
    """Method to run a dft calculation on the initial request payload."""
    logger.info("Starting dft calculation!")

    # Hopefully your model is more sophisticated!
    # build the input structure with gto
    # spin in pyscf is 2S not 2S+1
    s = dft_input.spin_multiplicity - 1
    mole = M(
        atom=str(dft_input.molecule),
        basis=dft_input.basis_set,
        charge=dft_input.charge,
        spin=s,
    )

    # run the dft calculation for the given functional
    fn = UKS if dft_input.spin_multiplicity > 1 else RKS
    calc = fn(mole)
    calc.xc = dft_input.functional
    _ = calc.kernel()

    logger.info("Finished dft calculation!")

    assert isinstance(calc.mo_energy, np.ndarray)
    assert isinstance(calc.mo_occ, np.ndarray)

    return SinglePointEnergyResponse(
        energy=calc.e_tot,
        converged=calc.converged,
        orbitals=[
            Orbital(energy=energy, occupancy=occ)
            for energy, occ in zip(
                calc.mo_energy,
                calc.mo_occ,
                strict=True,
            )
        ],
    )
