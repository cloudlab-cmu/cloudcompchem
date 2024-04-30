import logging

import pytest

from cloudcompchem.models import FunctionalConfig, SinglePointEnergyResponse

logger = logging.getLogger(__file__)


@pytest.fixture()
def config():
    yield FunctionalConfig(basis_set="ccpvdz", functional="pbe,pbe")


def test_local_client(local_sdk_client, mol, config, match_mol, caplog, expected_energy_response):
    caplog.set_level(logging.DEBUG)
    resp = local_sdk_client.single_point_energy(mol, config)
    logger.debug(f"resp = {resp}")
    assert isinstance(resp, SinglePointEnergyResponse)

    match_mol(resp, expected_energy_response)


def test_cloud_client(sdk_client, mol, config, match_mol, caplog, expected_energy_response):
    caplog.set_level(logging.DEBUG)
    resp = sdk_client.single_point_energy(mol, config)
    logger.debug(f"resp = {resp}")
    assert isinstance(resp, SinglePointEnergyResponse)

    match_mol(resp, expected_energy_response)
