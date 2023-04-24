#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Configure integration test run."""

import pathlib

from helpers import CONFIG, ZIP
from pytest import fixture
from pytest_operator.plugin import OpsTest


@fixture(scope="module")
async def glauth_charm(ops_test: OpsTest):
    """Build glauth charm to use for integration tests."""
    charm = await ops_test.build_charm(".")
    return charm


def pytest_sessionfinish(session, exitstatus) -> None:
    """Clean up repository after test session has completed."""
    pathlib.Path(CONFIG).unlink(missing_ok=True)
    pathlib.Path(ZIP).unlink(missing_ok=True)
