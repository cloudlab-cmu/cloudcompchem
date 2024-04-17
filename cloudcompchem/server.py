import argparse
import logging
import os

from flask import Flask
from gunicorn.app.base import BaseApplication
from pysll import Constellation

from cloudcompchem.controllers import DFTController


def create_app(constellation: Constellation | None = None) -> Flask:
    app = Flask(__name__)

    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

    # Configure the DFT controller
    dft_controller = DFTController(app.logger, constellation or Constellation())

    app.add_url_rule("/health-check", "healthcheck", dft_controller.health_check, methods=["GET"])
    app.add_url_rule("/energy", "energy", dft_controller.simulate_energy, methods=["POST"])
    return app


class FlaskApp(BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        assert self.cfg
        for key, value in self.options.items():
            self.cfg.set(key, value)

    def load(self):
        return self.application


def serve(args: argparse.Namespace):
    FlaskApp(
        create_app(),
        {
            "bind": args.bind,
            "workers": args.workers,
            "loglevel": os.environ.get("LOG_LEVEL", "INFO"),
            "timeout": 90,
        },
    ).run()
