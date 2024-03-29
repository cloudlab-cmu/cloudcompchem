from cloudcompchem.models import DFTRequest, SinglePointEnergyResponse
from pyscf import gto, dft
import logging

_logger = logging.getLogger("DFT-CALCULATOR")


def run_dft_calculation(dft_input: DFTRequest) -> SinglePointEnergyResponse:
    """Method to run a dft calculation on the initial request payload."""
    _logger.info("Starting dft calculation!")

    # Hopefully your model is more sophisticated!
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
    calc.xc = dft_input.functional
    energy = calc.kernel()
    _logger.info("Finished dft calculation!")

    return SinglePointEnergyResponse(energy=energy)


def find_homo_lumo(energies: list[float], occs: list[float]) -> tuple[float, float]:
    """Find the HOMO and LUMO energies from a list of orbital energy and
    occupancies."""

    # infer the threshold from the first occupancy value
    # if it's greater than 1, we're looking at a restricted calculation result
    # if not it's an unrestricted one
    if occs[0] > 1.0:
        thresh = 1.0
    else:
        thresh = 0.5
    lumo_index = len(list(filter(lambda occ: occ > thresh, occs)))
    return (energies[lumo_index - 1], energies[lumo_index])
