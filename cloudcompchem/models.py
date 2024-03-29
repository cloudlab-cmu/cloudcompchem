from __future__ import annotations
from dataclasses import dataclass
from .exceptions import ValidationException
from cloudcompchem.utils import find_homo_lumo


@dataclass
class Base:
    def __post_init__(self):
        self.validate()

    def validate(self):
        raise NotImplementedError


@dataclass
class DFTRequest(Base):
    calculator: Calculator
    molecule: Molecule

    def validate(self):
        if not isinstance(self.calculator, Calculator):
            raise ValidationException(
                "The calculator must be have the base of a Calculator class."
            )
        if not isinstance(self.molecule, Molecule):
            raise ValidationException(
                "The molecule must have the base of a Molecule class."
            )

    @staticmethod
    def from_dict(d: dict) -> DFTRequest:
        """Create a DFTRequest object from a json-like dictionary, which
        typically comes from a web request.
        """
        # unpack the nested molecule struct first
        mol_dict = d.pop("molecule", None)
        if mol_dict is None:
            raise ValidationException("No molecule information contained in request.")
        if not isinstance(mol_dict, dict):
            raise ValidationException(
                "Molecule information in request is not in JSON format."
            )
        mol = Molecule.from_dict(mol_dict)

        # unpack the calculator details next
        calc_dict = d.pop("calculator", None)
        if calc_dict is None:
            raise ValidationException("No calculator information contained in request.")
        if not isinstance(calc_dict, dict):
            raise ValidationException(
                "Calculation information in request is not in JSON format."
            )
        try:
            calc = Calculator(**calc_dict)
        except TypeError as te:
            # NOTE: type errors store the message in the first element of the args field
            raise ValidationException(te.args[0])

        # curry the unpacked molecule into the request instantiation and then add
        # the rest of the args by unpacking the initial dict
        return DFTRequest(calculator=calc, molecule=mol)


@dataclass
class Molecule(Base):
    spin_multiplicity: int
    charge: int
    atoms: list[Atom]

    def __str__(self) -> str:
        """Create a string representation that fits into the input for pyscf"""
        return "; ".join(str(a) for a in self.atoms)

    def validate(self):
        if not isinstance(self.spin_multiplicity, int):
            raise ValidationException("Spin multiplicity must be an int.")
        if not isinstance(self.charge, int):
            raise ValidationException("Charge must be an int.")
        if not isinstance(self.atoms, list):
            raise ValidationException("Atoms must be in a list.")
        if not all(isinstance(a, Atom) for a in self.atoms):
            raise ValidationException(
                "Each of the elements of the atoms argument must be an Atom."
            )

    @staticmethod
    def from_dict(d: dict) -> Molecule:
        """method that converts a dict from a json request into an object of
        this class.
        """
        atom_dicts = d.get("atoms")
        if atom_dicts is None:
            raise ValidationException("No 'atoms' key found in the molecule.")
        if not isinstance(atom_dicts, list):
            raise ValidationException("The value of the 'atoms' key is not a list.")
        return Molecule(atoms=[Atom(**a) for a in atom_dicts])


@dataclass
class Atom(Base):
    symbol: str
    position: list[float, float, float]

    def __str__(self) -> str:
        """Create a string representation for this atom that is an element of
        the molecular structure input for pyscf
        """
        return f"{self.symbol} {self.position[0]} {self.position[1]} {self.position[2]}"

    def validate(self):
        if not isinstance(self.symbol, str):
            raise ValidationException("Symbol must be a string.")
        if not isinstance(self.position, list):
            raise ValidationException("Atomic position must be a list.")
        if not len(self.position) == 3:
            raise ValidationException("Atomic positions must be 3 elements long.")
        if not all(isinstance(p, float | int) for p in self.position):
            raise ValidationException("Each value in the position must be a number.")


@dataclass
class SinglePointEnergyResponse:
    energy: float


@dataclass
class StructureRelaxationResponse:
    molecule: Molecule
    energy: float


@dataclass
class Calculator(Base):
    functional: str
    basis_set: str

    def validate(self):
        if not isinstance(self.functional, str):
            raise ValidationException("The functional must be a string.")
        if not isinstance(self.basis_set, str):
            raise ValidationException("The basis set must be a string.")


class EnergyCalculation:
    """Object that contains relevant energy calculation results and values,
    such as total energy, orbital energies, and occupancies.

    Attributes
    ----------
    total_energy : float
        The total energy of the molecule.
    orbital_energies : list[float]
        The individual energies for each calculated orbital.
    orbital_occupancies : list[float]
        The occupation numbers for each orbital.
    converged : bool
        Whether or not the calculation converged to an energetic minimum.
    homo : float
        The highest occupied molecular orbital energy
    lumo : float
        The lowest unoccupied molecular orbital energy
    gap : float
        The energy difference between the homo and lumo.
    """

    def __init__(self, resp: SinglePointEnergyResponse):
        self.total_energy = resp.energy
        self.orbital_energies = resp.orbital_energies
        self.orbital_occupancies = resp.orbital_occupancies
        self.converged = resp.converged
        # infer the homo, lumo, and gap from results
        self.homo, self.lumo = find_homo_lumo(
            self.orbital_energies, self.orbital_occupancies
        )
        self.gap = self.lumo - self.homo
