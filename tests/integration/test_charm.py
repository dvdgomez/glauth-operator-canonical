#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Test glauth charm."""

import asyncio

import pytest
from helpers import get_glauth_res
from pytest_operator.plugin import OpsTest

BASES = ["jammy"]
GLAUTH = "glauth"
SSSD = "sssd"
UBUNTU = "ubuntu"
JUJU_INFO = "juju-info"
LDAP_CLIENT = "ldap-client"


@pytest.mark.abort_on_fail
@pytest.mark.parametrize("bases", BASES)
@pytest.mark.skip_if_deployed
async def test_deploy(ops_test: OpsTest, bases: str, glauth_charm):
    """Test glauth charm deployment with sssd."""
    res_glauth = get_glauth_res()

    # Build and Deploy glauth
    await asyncio.gather(
        ops_test.model.deploy(
            str(await glauth_charm),
            application_name=GLAUTH,
            num_units=1,
            resources=res_glauth,
            bases=bases,
        ),
        ops_test.model.deploy(
            SSSD,
            application_name=SSSD,
            channel="edge",
            num_units=1,
            bases=bases,
        ),
        ops_test.model.deploy(
            UBUNTU,
            application_name=UBUNTU,
            channel="edge",
            num_units=1,
            bases=bases,
        ),
    )
    # Attach resource to charm
    await ops_test.juju("attach-resource", GLAUTH, f"config={res_glauth['config']}")
    # Set glauth config
    await ops_test.model.applications[GLAUTH].set_config({"ldap-search-base": "dc=glauth,dc=com"})
    # Run set-confidential action
    action = (
        await ops_test.model.applications[GLAUTH]
        .units[0]
        .run_action(
            "set-confidential",
            **{
                "ldap-password": "mysecret",
                "ldap-default-bind-dn": "cn=serviceuser,ou=svcaccts,dc=glauth,dc=com",
            },
        )
    )
    await action.wait()
    # Set relations for charmed applications
    await ops_test.model.integrate(f"{SSSD}:{JUJU_INFO}", f"{UBUNTU}:{JUJU_INFO}")
    await ops_test.model.integrate(f"{GLAUTH}:{LDAP_CLIENT}", f"{SSSD}:{LDAP_CLIENT}")
    # issuing update_status just to trigger an event
    async with ops_test.fast_forward():
        await ops_test.model.wait_for_idle(apps=[GLAUTH], status="active", timeout=1000)
        await ops_test.model.wait_for_idle(apps=[SSSD], status="active", timeout=1000)
        assert ops_test.model.applications[GLAUTH].units[0].workload_status == "active"


@pytest.mark.abort_on_fail
async def test_user_is_present(ops_test: OpsTest):
    """Test that user is present."""
    unit = ops_test.model.applications[SSSD].units[0]
    cmd_id = (await unit.ssh(command="id johndoe")).strip("\n")
    assert cmd_id == "uid=5002(johndoe) gid=5501(superheros) groups=5501(superheros)"
    cmd_get = (await unit.ssh(command="getent passwd johndoe")).strip("\n")
    assert cmd_get == "johndoe:*:5002:5501:johndoe:/:/bin/sh"
