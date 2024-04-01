from __future__ import annotations

import logging
from dataclasses import dataclass

from pyscf.dft import RKS, UKS

from cloudcompchem.exceptions import DFTRequestValidationException
from cloudcompchem.models import Molecule
from cloudcompchem.utils import M

logger = logging.getLogger("cloudcompchem.dft")


@dataclass
class Request:
    functional: str
    basis_set: str
    spin_multiplicity: int
    charge: int
    molecule: Molecule

    @staticmethod
    def from_dict(d: dict) -> Request:
        """Create a DFTRequest object from a json-like dictionary, which
        typically comes from a web request."""
        # unpack the nested molecule struct first
        molecule_data = d.pop("molecule")
        if not molecule_data:
            raise ValueError("No molecule information contained in request.")

        if not isinstance(d.get("charge"), int):
            raise DFTRequestValidationException("Charge must be an integer.")

        return Request(molecule=Molecule.from_dict(molecule_data), **d)


def calculate_energy(dft_input: Request) -> float:
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
    energy = calc.kernel()
    assert isinstance(energy, float)

    logger.info("Finished dft calculation!")

    return energy