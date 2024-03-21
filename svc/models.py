from __future__ import annotations
from dataclasses import dataclass
from functools import partial


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
        typically comes from a web request.
        """
        # unpack the nested molecule struct first
        mol_dict = d.pop("molecule", None)
        if mol_dict is None:
            raise TypeError("No molecule information contained in request.")
        if not isinstance(mol_dict, dict):
            raise TypeError("Molecule information in request is not in JSON format.")
        mol = Molecule.from_dict(mol_dict)

        # curry the unpacked molecule into the request instantiation and then add
        # the rest of the args by unpacking the initial dict
        return partial(DFTRequest, molecule=mol)(**d)


@dataclass
class Molecule:
    atoms: list[Atom]

    def __str__(self) -> str:
        """Create a string representation that fits into the input for pyscf"""
        return "; ".join(str(a) for a in self.atoms)

    @staticmethod
    def from_dict(d: dict) -> Molecule:
        """method that converts a dict from a json request into an object of
        this class.
        """
        atom_dicts = dict.get("atoms")
        if atom_dicts is None:
            raise TypeError("No 'atoms' key found in the molecule.")
        if not isinstance(atom_dicts, list):
            raise TypeError("The value of the 'atoms' key is not a list.")
        return Molecule(atoms=[Atom(**a) for a in atom_dicts])


@dataclass
class Atom:
    symbol: str
    position: list[float, float, float]

    def __str__(self) -> str:
        """Create a string representation for this atom that is an element of
        the molecular structure input for pyscf
        """
        return f"{self.symbol} {self.position[0]} {self.position[1]} {self.position[2]}"


@dataclass
class SinglePointEnergyResponse:
    energy: float


@dataclass
class StructureRelaxationResponse:
    molecule: Molecule
    energy: float
