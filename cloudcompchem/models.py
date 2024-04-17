from __future__ import annotations

from dataclasses import dataclass
from functools import partial

from .exceptions import DFTRequestValidationException


@dataclass
class EnergyRequest:
    config: FunctionalConfig
    molecule: Molecule

    @staticmethod
    def from_dict(d: dict) -> EnergyRequest:
        """Create a DFTRequest object from a json-like dictionary, which
        typically comes from a web request."""
        # unpack the nested molecule struct first
        mol_dict = d.pop("molecule", None)
        if not mol_dict:
            raise DFTRequestValidationException("No molecule information contained in request.")
        if not isinstance(mol_dict, dict):
            raise DFTRequestValidationException("Molecule information in request is not in JSON format.")
        molecule = Molecule.from_dict(mol_dict)

        # TODO: switch our dataclasses to pydantic BaseModels
        if not isinstance(mol_dict.get("charge"), int):
            raise DFTRequestValidationException("Charge must be an integer.")
        if not isinstance(mol_dict.get("spin_multiplicity"), int):
            raise DFTRequestValidationException("Spin multiplicity must be an integer.")

        # get the functional config
        config_dict = d.get("config")
        if config_dict is None:
            raise DFTRequestValidationException(
                "No functional configuration has been specified (use the 'config' keyword)."
            )
        config = FunctionalConfig(**config_dict)

        return EnergyRequest(config=config, molecule=molecule)


@dataclass
class FunctionalConfig:
    functional: str
    basis_set: str


@dataclass
class Molecule:
    atoms: list[Atom]
    spin_multiplicity: int
    charge: int

    def __str__(self) -> str:
        """Create a string representation that fits into the input for
        pyscf."""
        return "; ".join(str(a) for a in self.atoms)

    @staticmethod
    def from_dict(d: dict) -> Molecule:
        """Method that converts a dict from a json request into an object of
        this class."""
        atom_dicts = d.pop("atoms", None)
        if atom_dicts is None:
            raise DFTRequestValidationException("No 'atoms' key found in the molecule.")
        if not isinstance(atom_dicts, list):
            raise DFTRequestValidationException("The value of the 'atoms' key is not a list.")
        atoms = [Atom(**a) for a in atom_dicts]
        return partial(Molecule, atoms=atoms)(**d)


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
