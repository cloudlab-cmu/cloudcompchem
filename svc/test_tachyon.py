from flask import Flask

import logging

from controller import DFTController

app = Flask(__name__)


def test_health_check():
    tachyon = Tachyon(logging.getLogger("Tachyon"), MockConstellation())
    with app.test_request_context("/health-check"):
        assert tachyon.health_check().get_json() == {"message": "OK"}


def test_shutdown():
    tachyon = Tachyon(logging.getLogger("Tachyon"), MockConstellation())
    with app.test_request_context("/shutdown"):
        assert tachyon.shutdown().get_json() == {"message": "OK"}


def test_train():
    tachyon = Tachyon(logging.getLogger("Tachyon"), MockConstellation())
    with app.test_request_context(
        "/train",
        method="POST",
        json={
            "datasets": ["id:dataset1", "id:dataset2"],
            "simulation": "id:simulation",
        },
        headers={"Authorization": "Bearer validAuthToken"},
    ):
        assert tachyon.train().get_json() == {"message": "OK"}
        assert tachyon.shutdown().get_json() == {"message": "OK"}


def test_simulate():
    tachyon = Tachyon(logging.getLogger("Tachyon"), MockConstellation())
    with app.test_request_context(
        "/simulate",
        method="POST",
        json={
            "protocols": ["id:protocol1", "id:protocol2"],
            "simulation": "id:simulation",
        },
        headers={"Authorization": "Bearer validAuthToken"},
    ):
        assert tachyon.simulate().get_json() == {"message": "OK"}
        assert tachyon.shutdown().get_json() == {"message": "OK"}


class MockConstellation:
    def download(self, auth_token, object_id, fields):
        mock_object = mock_objects_by_id.get(object_id, {})
        return {field: mock_object.get(field) for field in fields}


mock_objects_by_id = {
    "id:dataset1": {
        "ID": "id:dataset1",
        "Type": "Object.TrainingDataset",
        "Name": "First Training Set",
    },
    "id:dataset2": {
        "ID": "id:dataset2",
        "Type": "Object.TrainingDataset",
        "Name": "Second Training Set",
    },
    "id:simulation": {
        "ID": "id:simulation",
        "Type": "Object.Simulation",
        "Name": "My First Simulation",
    },
    "id:protocol1": {
        "ID": "id:protocol1",
        "Type": "Object.Protocol.TestProtocol",
        "Name": "First Protocol",
        "Status": "Processing",
    },
    "id:protocol2": {
        "ID": "id:protocol2",
        "Type": "Object.Protocol.TestProtocol",
        "Name": "Second Protocol",
        "Status": "Processing",
    },
}
