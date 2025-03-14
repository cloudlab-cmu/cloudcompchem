import logging

import numpy as np
from pyscf.dft import RKS, UKS
from pyscf.geomopt.berny_solver import optimize as berny_opt
from pyscf.geomopt.geometric_solver import optimize as geomeTRIC_opt
from pyscf.hessian import thermo
from pyscf.hessian.rhf import Hessian

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
    """Method to run a DFT optimization on the initial request payload and
    calculate frequencies."""
    logger.info("Starting DFT optimization!")

    # Set up molecule
    s = dft_input.molecule.spin_multiplicity - 1
    mol = M(
        atom=str(dft_input.molecule),
        basis=dft_input.config.basis_set,
        charge=dft_input.molecule.charge,
        spin=s,
    )

    # Choose RKS or UKS based on spin multiplicity
    fn = UKS if dft_input.molecule.spin_multiplicity > 1 else RKS
    calc = fn(mol)
    calc.xc = dft_input.config.functional

    # Run geometry optimization
    optimizer = optimizers[dft_input.solver_config.solver]
    mol_eq = optimizer(method=calc, **dft_input.solver_config.conv_params)
    energy = calc.kernel()
    assert energy is not None

    # Frequency and Hessian calculation
    hessian_calculator = Hessian(calc)
    hessian_matrix = hessian_calculator.kernel()
    frequencies = thermo.harmonic_analysis(mol, hess=hessian_matrix)

    logger.info("Finished DFT optimization and frequency calculation!")

    # Prepare response
    list_of_atoms = [Atom(atom, tuple(np.round(position, 7))) for atom, position in mol_eq.atom]
    charge, spin_multiplicity = dft_input.molecule.charge, dft_input.molecule.spin_multiplicity
    response_mol = Molecule(list_of_atoms, spin_multiplicity=spin_multiplicity, charge=charge)

    assert isinstance(calc.mo_energy, np.ndarray)
    assert isinstance(calc.mo_occ, np.ndarray)

    energies = map(float, calc.mo_energy)
    occupancies = map(float, calc.mo_occ)

    return StructureRelaxationResponse(
        molecule=response_mol,
        energy=energy,
        converged=calc.converged,
        orbitals=[Orbital(energy=energy, occupancy=occ) for energy, occ in zip(energies, occupancies, strict=True)],
        hessian=hessian_matrix,
        frequencies=frequencies,
    )
