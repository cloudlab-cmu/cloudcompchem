from cloudcompchem.models import StructureRelaxationResponse, DFTOptRequest
from pyscf import gto, dft
import logging

_logger = logging.getLogger("DFT-CALCULATOR")

def run_dft_opt(dft_input: DFTOptRequest) -> StructureRelaxationResponse:

    """Method to run a dft optimization on the initial request payload."""
    _logger.info("Starting dft optimization!")
    # build the input structure with gto
    # spin in pyscf is 2S not 2S+1
    s = dft_input.spin_multiplicity - 1
    mol = gto.M(
        atom=str(dft_input.molecule),
        basis=dft_input.basis_set,
        charge=dft_input.charge,
        spin=s,
    )

    # run the dft calculation for the given functional
    if dft_input.spin_multiplicity > 1:
        # use unrestricted kohn-sham
        calc = dft.UKS(mol)
    else:
        calc = dft.RKS(mol)
    mol_eq = calc.Gradients().optimizer(solver=dft_input.solver).kernel()
    energy = calc.kernel()
    _logger.info("Finished dft optimization!")
    response_mol = {"atoms":[{"symbol":i[0], "position":i[1]} for i in mol_eq.atom]}

    return StructureRelaxationResponse(molecule=response_mol, energy=energy) 