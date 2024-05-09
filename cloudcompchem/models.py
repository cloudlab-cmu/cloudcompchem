from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from typing import Literal, get_args

from .exceptions import (
    DFTRequestValidationException,
    MoleculeSpinAndChargeViolationError,
)

AtomSymbol = Literal[
    "H",
    "He",
    "Li",
    "Be",
    "B",
    "C",
    "N",
    "O",
    "F",
    "Ne",
    "Na",
    "Mg",
    "Al",
    "Si",
    "P",
    "S",
    "Cl",
    "Ar",
    "K",
    "Ca",
    "Sc",
    "Ti",
    "V",
    "Cr",
    "Mn",
    "Fe",
    "Co",
    "Ni",
    "Cu",
    "Zn",
    "Ga",
    "Ge",
    "As",
    "Se",
    "Br",
    "Kr",
    "Rb",
    "Sr",
    "Y",
    "Zr",
    "Nb",
    "Mo",
    "Tc",
    "Ru",
    "Rh",
    "Pd",
    "Ag",
    "Cd",
    "In",
    "Sn",
    "Sb",
    "Te",
    "I",
    "Xe",
    "Cs",
    "Ba",
    "La",
    "Ce",
    "Pr",
    "Nd",
    "Pm",
    "Sm",
    "Eu",
    "Gd",
    "Tb",
    "Dy",
    "Ho",
    "Er",
    "Tm",
    "Yb",
    "Lu",
    "Hf",
    "Ta",
    "W",
    "Re",
    "Os",
    "Ir",
    "Pt",
    "Au",
    "Hg",
    "Tl",
    "Pb",
    "Bi",
    "Po",
    "At",
    "Rn",
    "Fr",
    "Ra",
    "Ac",
    "Th",
    "Pa",
    "U",
    "Np",
    "Pu",
    "Am",
    "Cm",
    "Bk",
    "Cf",
]

ATOMIC_NUMBERS: dict[AtomSymbol, int] = {atom: position for position, atom in enumerate(get_args(AtomSymbol), start=1)}

# make sure we didn't miss any symbols
assert len(ATOMIC_NUMBERS) == 98


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

    def __post_init__(self):
        if not isinstance(self.charge, int):
            raise DFTRequestValidationException("charge must be an integer")
        if not isinstance(self.spin_multiplicity, int):
            raise DFTRequestValidationException("spin multiplicity must be an integer")

        charge, spin = self.charge, (self.spin_multiplicity - 1) % 2
        total_e = sum(ATOMIC_NUMBERS[atom.symbol] for atom in self.atoms) - charge
        total_e %= 2
        if total_e != spin:
            raise MoleculeSpinAndChargeViolationError(self.spin_multiplicity, self.charge)

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
    symbol: AtomSymbol
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

    @staticmethod
    def from_dict(d: dict) -> SinglePointEnergyResponse:
        orbital_info = d["orbitals"]
        orbitals = [Orbital(**kwargs) for kwargs in orbital_info]
        return SinglePointEnergyResponse(orbitals=orbitals, converged=d["converged"], energy=d["energy"])


geometric_conv_params = {  # These are the default settings
    "convergence_energy": 1e-6,  # Eh
    "convergence_grms": 3e-4,  # Eh/Bohr
    "convergence_gmax": 4.5e-4,  # Eh/Bohr
    "convergence_drms": 1.2e-3,  # Angstrom
    "convergence_dmax": 1.8e-3,  # Angstrom
}

berny_conv_params = {  # These are the default settings
    "gradientmax": 0.45e-3,  # Eh/[Bohr|rad]
    "gradientrms": 0.15e-3,  # Eh/[Bohr|rad]
    "stepmax": 1.8e-3,  # [Bohr|rad]
    "steprms": 1.2e-3,  # [Bohr|rad]
}

DEFAULT_CONV_PARAMS = {"geomeTRIC": geometric_conv_params, "berny": berny_conv_params}


@dataclass
class SolverConfig:
    solver: str
    conv_params: dict


@dataclass
class DFTOptRequest:
    config: FunctionalConfig
    molecule: Molecule
    solver_config: SolverConfig

    @staticmethod
    def from_dict(d: dict) -> DFTOptRequest:
        """Create a DFTOptRequest object from a json-like dictionary, which
        typically comes from a web request."""
        # unpack the nested molecule struct first
        mol_dict = d.pop("molecule", None)
        if mol_dict is None:
            raise DFTRequestValidationException("No molecule information contained in request.")
        if not isinstance(mol_dict, dict):
            raise DFTRequestValidationException("Molecule information in request is not in JSON format.")
        molecule = Molecule.from_dict(mol_dict)

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

        if d.get("solver") not in ["geomeTRIC", "berny"]:
            raise DFTRequestValidationException("Only geomeTRIC and berny are supported.")
        # parse the convergence parameters and create a complete dictionary of convergence parameters to be passed
        # note that this will be solver-specific
        base_conv_params = d.pop("conv_params", None)
        default_conv_params_copy = DEFAULT_CONV_PARAMS[d["solver"]].copy()
        if isinstance(base_conv_params, dict):
            for key in base_conv_params:
                if key in default_conv_params_copy:
                    default_conv_params_copy[key] = base_conv_params[key]
                else:
                    raise DFTRequestValidationException(f"Convergence parameter {key} is not supported.")
        solver = d.pop("solver", None)
        solver_config = SolverConfig(solver, default_conv_params_copy)

        # curry the unpacked molecule into the request instantiation and then add
        # the rest of the args by unpacking the initial dict
        return DFTOptRequest(config=config, molecule=molecule, solver_config=solver_config)


@dataclass
class StructureRelaxationResponse:
    molecule: Molecule
    energy: float
    converged: bool
    orbitals: list[Orbital]

    @staticmethod
    def from_dict(d: dict) -> StructureRelaxationResponse:
        orbital_info = d["orbitals"]
        orbitals = [Orbital(**kwargs) for kwargs in orbital_info]
        return StructureRelaxationResponse(
            orbitals=orbitals, converged=d["converged"], energy=d["energy"], molecule=d["molecule"]
        )
