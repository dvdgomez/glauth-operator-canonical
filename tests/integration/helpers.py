#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Helpers for the glauth integration tests."""

import logging
import pathlib
import zipfile
from typing import Dict
from urllib import request

import toml

logger = logging.getLogger(__name__)

CONFIG = "sample-simple.cfg"
CONFIG_URL = (
    f"https://github.com/glauth/glauth/raw/0e7769ff841e096dbf0cb67768cbd2ab7142f6fb/v2/{CONFIG}"
)
ZIP = "config.zip"


def get_glauth_res() -> Dict[str, pathlib.Path]:
    """Get glauth resources needed for charm deployment."""
    if not (zip := pathlib.Path(ZIP)).exists():
        logger.info(f"Getting resource {CONFIG} from {CONFIG_URL}...")
        request.urlretrieve(CONFIG_URL, CONFIG)

        # Update config for integration test
        assert pathlib.Path(CONFIG).exists()
        with open(CONFIG, "r") as f:
            config_dict = toml.load(f)
        config_dict["ldaps"].update({"listen": "0.0.0.0:636", "enabled": True})
        config_dict["backend"].update({"anonymousdse": True})
        config_dict["users"][1].update({"homeDir": "/"})

        with zipfile.ZipFile(ZIP, "w") as z:
            z.writestr("sample-simple.cfg", toml.dumps(config_dict))

    return {"config": zip}
