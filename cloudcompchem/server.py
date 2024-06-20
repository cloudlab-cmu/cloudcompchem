import argparse
import logging
import os
import random

from celery import Celery, Task
from flask import Flask, request
from gunicorn.app.base import BaseApplication
from pysll import Constellation

from cloudcompchem.controllers import DFTController
from cloudcompchem.tasks import add_together


def create_app(constellation: Constellation | None = None) -> Flask:
    app = Flask(__name__)

    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

    # Configure the DFT controller
    dft_controller = DFTController(app.logger, constellation or Constellation())

    app.add_url_rule("/health-check", "healthcheck", dft_controller.health_check, methods=["GET"])
    app.add_url_rule("/energy", "energy", dft_controller.simulate_energy, methods=["POST"])
    app.add_url_rule("/opt", "geom opt", dft_controller.geom_opt, methods=["POST"])
    app.add_url_rule("/aadd", "aadd", async_add, methods=["POST"])
    app.add_url_rule("/result/<id>", "result", result)

    # celery
    app.config.from_mapping(
        CELERY=dict(
            broker_url=f"redis://{os.environ.get('CLOUDCOMPCHEM_REDIS_URL', 'localhost')}",
            result_backend=f"redis://{os.environ.get('CLOUDCOMPCHEM_REDIS_URL', 'localhost')}",
            task_ignore_result=True,
        ),
    )
    app.config.from_prefixed_env()
    celery_init_app(app)

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


def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app


def async_add() -> dict[str, object]:
    a = request.form.get("a", default=random.randint(0, 100), type=int)
    b = request.form.get("b", default=random.randint(0, 100), type=int)
    result = add_together.delay(a, b)  # pyright:ignore
    return {"result_id": result.id}


def result(id: str) -> dict[str, object]:
    from celery.result import AsyncResult

    result = AsyncResult(id)
    return {
        "ready": result.ready(),
        "successful": result.successful(),
        "value": result.result if result.ready() else None,
    }
