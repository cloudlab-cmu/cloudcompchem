from __future__ import annotations

import logging

import numpy as np
from pyscf.dft import RKS, UKS

from cloudcompchem.models import EnergyRequest, Orbital, SinglePointEnergyResponse
from cloudcompchem.utils import M

logger = logging.getLogger("cloudcompchem.dft")


def calculate_energy(dft_input: EnergyRequest) -> SinglePointEnergyResponse:
    """Method to run a dft calculation on the initial request payload."""
    logger.info("Starting dft calculation!")

    # Hopefully your model is more sophisticated!
    # build the input structure with gto
    # spin in pyscf is 2S not 2S+1
    s = dft_input.molecule.spin_multiplicity - 1
    mole = M(
        atom=str(dft_input.molecule),
        basis=dft_input.config.basis_set,
        charge=dft_input.molecule.charge,
        spin=s,
    )

    # run the dft calculation for the given functional
    fn = UKS if dft_input.molecule.spin_multiplicity > 1 else RKS
    calc = fn(mole)
    calc.xc = dft_input.config.functional
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
