from cloudcompchem.models import StructureRelaxationResponse, DFTOptRequest, Atom, Molecule
from cloudcompchem.utils import M

from pyscf.dft import RKS, UKS
from pyscf.geomopt.geometric_solver import optimize as geomeTRIC_opt
from pyscf.geomopt.berny_solver import optimize as berny_opt
import logging
import numpy as np

optimizers = {'geomeTRIC':geomeTRIC_opt, 'berny':berny_opt}

_logger = logging.getLogger("DFT-CALCULATOR")

def run_dft_opt(dft_input: DFTOptRequest) -> StructureRelaxationResponse:

    """Method to run a dft optimization on the initial request payload."""
    _logger.info("Starting dft optimization!")
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
    _logger.info("Finished dft optimization!")
    list_of_atoms = [Atom(atom, list(np.round(position, 7))) for atom, position in mol_eq.atom]
    response_mol = Molecule(list_of_atoms)

    return StructureRelaxationResponse(molecule=response_mol, energy=energy) 