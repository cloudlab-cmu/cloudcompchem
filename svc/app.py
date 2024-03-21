#!/usr/bin/env python3

import logging

from pysll import Constellation
from flask import Flask

from .controller import DFTController


# This is run automatically by flask when the application starts
def create_app(constellation=Constellation()):
    app = Flask(__name__, instance_relative_config=False)

    # Setup logging
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

    # Configure the tachyon controller
    dft_controller = DFTController(app.logger, constellation)

    app.add_url_rule(
        "/health-check", "healthcheck", dft_controller.health_check, methods=["GET"]
    )
    app.add_url_rule(
        "/energy", "energy", dft_controller.simulate_energy, methods=["POST"]
    )

    return app
