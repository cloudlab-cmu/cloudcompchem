from __future__ import annotations

from dataclasses import dataclass
from functools import partial

from .exceptions import DFTRequestValidationException

atomic_numbers = {'H': 1, 'He': 2, 'Li': 3, 'Be': 4, 'B': 5, 'C': 6, 'N': 7, 'O': 8, 'F': 9, 'Ne': 10, 'Na': 11, 'Mg': 12, 'Al': 13, 'Si': 14,
'P': 15, 'S': 16, 'Cl': 17, 'Ar': 18, 'K': 19, 'Ca': 20, 'Sc': 21, 'Ti': 22, 'V': 23, 'Cr': 24, 'Mn': 25, 'Fe': 26, 'Co': 27, 'Ni': 28,
'Cu': 29, 'Zn': 30, 'Ga': 31, 'Ge': 32, 'As': 33, 'Se': 34, 'Br': 35, 'Kr': 36, 'Rb': 37, 'Sr': 38, 'Y': 39, 'Zr': 40, 'Nb': 41, 'Mo': 42,
'Tc': 43, 'Ru': 44, 'Rh': 45, 'Pd': 46, 'Ag': 47, 'Cd': 48, 'In': 49, 'Sn': 50, 'Sb': 51, 'Te': 52, 'I': 53, 'Xe': 54, 'Cs': 55, 'Ba': 56,
'La': 57, 'Ce': 58, 'Pr': 59, 'Nd': 60, 'Pm': 61, 'Sm': 62, 'Eu': 63, 'Gd': 64, 'Tb': 65, 'Dy': 66, 'Ho': 67, 'Er': 68, 'Tm': 69, 'Yb': 70,
'Lu': 71, 'Hf': 72, 'Ta': 73, 'W': 74, 'Re': 75, 'Os': 76, 'Ir': 77, 'Pt': 78, 'Au': 79, 'Hg': 80, 'Tl': 81, 'Pb': 82, 'Bi': 83, 'Po': 84,
'At': 85, 'Rn': 86, 'Fr': 87, 'Ra': 88, 'Ac': 89, 'Th': 90, 'Pa': 91, 'U': 92, 'Np': 93, 'Pu': 94, 'Am': 95, 'Cm': 96, 'Bk': 97, 'Cf': 98}

def check_charge_spin(molecule: Molecule):
    charge, spin = molecule.charge, molecule.spin_multiplicity
    atom_symbols = [atom.symbol for atom in Molecule.atoms]
    total_e = sum([atomic_numbers[symbol] for symbol in atom_symbols])
    total_e = total_e%2 - charge
    spin = (spin-1)%2
    try:
        assert total_e==spin
    except:
        raise DFTRequestValidationException(f"Combination of charge={charge} and spin multiplicity={spin} is not valid.")

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
        check_charge_spin(molecule=molecule)

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

    @staticmethod
    def from_dict(d: dict) -> SinglePointEnergyResponse:
        orbital_info = d["orbitals"]
        orbitals = [Orbital(**kwargs) for kwargs in orbital_info]
        return SinglePointEnergyResponse(orbitals=orbitals, converged=d["converged"], energy=d["energy"])

geometric_conv_params = { # These are the default settings
    'convergence_energy': 1e-6,  # Eh
    'convergence_grms': 3e-4,    # Eh/Bohr
    'convergence_gmax': 4.5e-4,  # Eh/Bohr
    'convergence_drms': 1.2e-3,  # Angstrom
    'convergence_dmax': 1.8e-3,  # Angstrom
}

berny_conv_params = {  # These are the default settings
    'gradientmax': 0.45e-3,  # Eh/[Bohr|rad]
    'gradientrms': 0.15e-3,  # Eh/[Bohr|rad]
    'stepmax': 1.8e-3,       # [Bohr|rad]
    'steprms': 1.2e-3,       # [Bohr|rad]
}

default_conv_params = {'geomeTRIC': geometric_conv_params, 'berny': berny_conv_params}

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
        typically comes from a web request.
        """
        # unpack the nested molecule struct first
        mol_dict = d.pop("molecule", None)
        if mol_dict is None:
            raise DFTRequestValidationException(
                "No molecule information contained in request."
            )
        if not isinstance(mol_dict, dict):
            raise DFTRequestValidationException(
                "Molecule information in request is not in JSON format."
            )
        molecule = Molecule.from_dict(mol_dict)
        check_charge_spin(molecule=molecule)

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
        
        if d.get("solver") not in ['geomeTRIC', 'berny']:
            raise DFTRequestValidationException("Only geomeTRIC and berny are supported.")
        # parse the convergence parameters and create a complete dictionary of convergence parameters to be passed
        # note that this will be solver-specific
        base_conv_params = d.pop("conv_params", None)
        default_conv_params_copy = default_conv_params[d.get("solver")].copy()
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
        return StructureRelaxationResponse(orbitals=orbitals, converged=d["converged"], energy=d["energy"], molecule=d['molecule'])
