from __future__ import annotations

from dataclasses import dataclass
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
            raise ValueError("No molecule information contained in request.")
        if not isinstance(mol_dict, dict):
            raise ValueError("Molecule information in request is not in JSON format.")

        molecule = Molecule.from_dict(mol_dict)

        # TODO: switch our dataclasses to pydantic BaseModels
        if not isinstance(mol_dict.get("charge"), int):
            raise ValueError("Charge must be an integer.")
        if not isinstance(mol_dict.get("spin_multiplicity"), int):
            raise ValueError("Spin multiplicity must be an integer.")

        try:
            config = FunctionalConfig(**d["config"])
        except (KeyError, TypeError) as err:
            raise ValueError("Invalid functional configuration") from err

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
        try:
            return Molecule(atoms=[Atom(**a) for a in d.pop("atoms")], **d)
        except (AttributeError, KeyError, TypeError) as err:
            raise ValueError from err


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


DEFAULT_CONV_PARAMS = {
    "geomeTRIC": {
        "convergence_energy": 1e-6,  # Eh
        "convergence_grms": 3e-4,  # Eh/Bohr
        "convergence_gmax": 4.5e-4,  # Eh/Bohr
        "convergence_drms": 1.2e-3,  # Angstrom
        "convergence_dmax": 1.8e-3,  # Angstrom
    },
    "berny": {
        "gradientmax": 0.45e-3,  # Eh/[Bohr|rad]
        "gradientrms": 0.15e-3,  # Eh/[Bohr|rad]
        "stepmax": 1.8e-3,  # [Bohr|rad]
        "steprms": 1.2e-3,  # [Bohr|rad]
    },
}


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

        try:
            molecule = Molecule.from_dict(d["molecule"])
        except KeyError:
            raise DFTRequestValidationException("No molecule information contained in request.") from None
        except ValueError as err:
            raise DFTRequestValidationException("Invalid molecule.") from err

        try:
            config = FunctionalConfig(**d["config"])
        except KeyError:
            raise DFTRequestValidationException(
                "No functional configuration has been specified (use the 'config' keyword)."
            ) from None
        except TypeError:
            raise DFTRequestValidationException("Invalid functional config") from None

        try:
            solver = d["solver"]
        except KeyError:
            raise DFTRequestValidationException("missing 'solver' key") from None

        conv_params = d.get("conv_params", {})
        if not isinstance(conv_params, dict):
            raise DFTRequestValidationException("invalid 'conv_params'")

        try:
            default_conv_params = DEFAULT_CONV_PARAMS[solver]
        except KeyError:
            raise DFTRequestValidationException(
                f"Only {', '.join(DEFAULT_CONV_PARAMS.keys())} are supported."
            ) from None

        if extra := set(conv_params) - set(default_conv_params):
            raise DFTRequestValidationException(
                f"Convergence parameter(s) [{', '.join(extra)}] is (are) not supported."
            )

        return DFTOptRequest(
            config=config,
            molecule=molecule,
            solver_config=SolverConfig(
                solver,
                default_conv_params | conv_params,
            ),
        )


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
