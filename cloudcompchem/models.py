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
        mol = Molecule.from_dict(mol_dict)

        if not isinstance(d.get("charge"), int):
            raise DFTRequestValidationException("Charge must be an integer.")

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
        atom_dicts = d.get("atoms")
        if atom_dicts is None:
            raise DFTRequestValidationException("No 'atoms' key found in the molecule.")
        if not isinstance(atom_dicts, list):
            raise DFTRequestValidationException(
                "The value of the 'atoms' key is not a list."
            )
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
class DFTOptRequest:
    functional: str
    basis_set: str
    spin_multiplicity: int
    charge: int
    molecule: Molecule
    solver: str
    conv_params: dict

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
        mol = Molecule.from_dict(mol_dict)

        if not isinstance(d.get("charge"), int):
            raise DFTRequestValidationException("Charge must be an integer.")
        
        if not isinstance(d.get("spin_multiplicity"), int):
            raise DFTRequestValidationException("Spin multiplicity must be an integer.")
        
        if d.get("solver") not in ['geomeTRIC', 'berny']:
            raise DFTRequestValidationException("Only geomeTRIC and berny are supported.")
        
        # parse the convergence parameters and create a complete dictionary of convergence parameters to be passed
        # note that this will be solver-specific
        base_conv_params = d["conv_params"].copy()
        default_conv_params_copy = default_conv_params[d.get("solver")].copy()
        for key in base_conv_params: 
            if key in default_conv_params_copy:
                default_conv_params_copy[key] = base_conv_params[key]
            else:
                raise DFTRequestValidationException(f"Convergence parameter {key} is not supported.")
        d["conv_params"] = base_conv_params

        # curry the unpacked molecule into the request instantiation and then add
        # the rest of the args by unpacking the initial dict
        return partial(DFTOptRequest, molecule=mol)(**d)

@dataclass
class StructureRelaxationResponse:
    molecule: dict
    energy: float
