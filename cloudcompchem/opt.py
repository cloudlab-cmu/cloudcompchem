import logging

import numpy as np
from pyscf.dft import RKS, UKS
from pyscf.geomopt.berny_solver import optimize as berny_opt
from pyscf.geomopt.geometric_solver import optimize as geomeTRIC_opt

from cloudcompchem.models import (
    Atom,
    DFTOptRequest,
    Molecule,
    Orbital,
    StructureRelaxationResponse,
)
from cloudcompchem.utils import M

optimizers = {"geomeTRIC": geomeTRIC_opt, "berny": berny_opt}

logger = logging.getLogger("cloudcompchem.opt")


def run_dft_opt(dft_input: DFTOptRequest) -> StructureRelaxationResponse:
    """Method to run a dft optimization on the initial request payload."""
    logger.info("Starting dft optimization!")
    # build the input structure with gto
    # spin in pyscf is 2S not 2S+1
    s = dft_input.molecule.spin_multiplicity - 1
    mol = M(
        atom=str(dft_input.molecule),
        basis=dft_input.config.basis_set,
        charge=dft_input.molecule.charge,
        spin=s,
    )

    # run the dft calculation for the given functional
    fn = UKS if dft_input.molecule.spin_multiplicity > 1 else RKS
    calc = fn(mol)
    calc.xc = dft_input.config.functional

    optimizer = optimizers[dft_input.solver_config.solver]
    mol_eq = optimizer(method=calc, **dft_input.solver_config.conv_params)
    energy = calc.kernel()
    assert energy is not None

    logger.info("Finished dft optimization!")
    list_of_atoms = [Atom(atom, tuple(np.round(position, 7))) for atom, position in mol_eq.atom]

    charge, spin_multiplicity = dft_input.molecule.charge, dft_input.molecule.spin_multiplicity
    response_mol = Molecule(list_of_atoms, spin_multiplicity=spin_multiplicity, charge=charge)

    assert isinstance(calc.mo_energy, np.ndarray)
    assert isinstance(calc.mo_occ, np.ndarray)
    energies = map(float, calc.mo_energy)
    occupancies = calc.mo_occ

    return StructureRelaxationResponse(
        molecule=response_mol,
        energy=energy,
        converged=calc.converged,
        orbitals=[Orbital(energy=energy, occupancy=occ) for energy, occ in zip(energies, occupancies, strict=True)],
    )
