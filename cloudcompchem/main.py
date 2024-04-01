import argparse
import json
import logging
import os
from typing import Callable, TypeAlias

from cloudcompchem import dft
from cloudcompchem.server import serve


def setup_logging():
    level = logging.getLevelName(os.environ.get("LOG_LEVEL", "INFO"))
    logging.getLogger().setLevel(level)


def energy(args: argparse.Namespace):
    with open(args.filename) as handle:
        data = json.load(handle)

    request = dft.Request.from_dict(data)
    output = dft.calculate_energy(request)

    print(output)


Cmd: TypeAlias = Callable[[argparse.Namespace], None]


def main() -> int:
    setup_logging()

    modes: dict[str, tuple[Callable[[argparse.ArgumentParser]], Cmd]] = {
        "serve": (
            lambda parser: (
                parser.add_argument("--bind", default="0.0.0.0:5000"),
                parser.add_argument("--workers", default=4),
            ),
            serve,
        ),
        "energy": (
            lambda parser: (parser.add_argument("filename"),),
            energy,
        ),
    }

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="mode")

    for mode, (setup, _) in modes.items():
        mode_parser = subparsers.add_parser(mode)
        setup(mode_parser)

    args = parser.parse_args()

    _, cmd = modes[args.mode]

    cmd(args)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
