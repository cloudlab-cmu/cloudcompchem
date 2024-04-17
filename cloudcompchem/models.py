from __future__ import annotations

from dataclasses import dataclass
from functools import partial

from .exceptions import DFTRequestValidationException


@dataclass
class DFTRequest:
    functional: str
    basis_set: str
    spin_multiplicity: int
    charge: int
    molecule: Molecule

    @staticmethod
    def from_dict(d: dict) -> DFTRequest:
        """Create a DFTRequest object from a json-like dictionary, which
        typically comes from a web request."""
        # unpack the nested molecule struct first
        mol_dict = d.pop("molecule", None)
        if not mol_dict:
            raise DFTRequestValidationException("No molecule information contained in request.")
        if not isinstance(mol_dict, dict):
            raise DFTRequestValidationException("Molecule information in request is not in JSON format.")
        molecule = Molecule.from_dict(mol_dict)

        if not isinstance(d.get("charge"), int):
            raise DFTRequestValidationException("Charge must be an integer.")
        # how come only "charge" gets validated? we could use pydantic!

        # curry the unpacked molecule into the request instantiation and then add
        # the rest of the args by unpacking the initial dict
        return partial(DFTRequest, molecule=molecule)(**d)


@dataclass
class Molecule:
    atoms: list[Atom]

    def __str__(self) -> str:
        """Create a string representation that fits into the input for
        pyscf."""
        return "; ".join(str(a) for a in self.atoms)

    @staticmethod
    def from_dict(d: dict) -> Molecule:
        """Method that converts a dict from a json request into an object of
        this class."""
        atom_dicts = d.get("atoms")
        if atom_dicts is None:
            raise DFTRequestValidationException("No 'atoms' key found in the molecule.")
        if not isinstance(atom_dicts, list):
            raise DFTRequestValidationException("The value of the 'atoms' key is not a list.")
        return Molecule(atoms=[Atom(**a) for a in atom_dicts])


@dataclass
class Atom:
    symbol: str
    position: tuple[float, float, float]

    def __str__(self) -> str:
        """Create a string representation for this atom that is an element of
        the molecular structure input for pyscf."""
        x, y, z = self.position
        return f"{self.symbol} {x} {y} {z}"


@dataclass
class Orbital:
    energy: float
    occupancy: float


@dataclass
class SinglePointEnergyResponse:
    energy: float
    converged: bool
    orbitals: list[Orbital]


@dataclass
class StructureRelaxationResponse:
    molecule: Molecule
    energy: float
