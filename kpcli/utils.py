#!/usr/bin/env python3
# standards
import configparser
import logging
from os import environ
from pathlib import Path

import typer

from kpcli.datastructures import KpConfig

logger = logging.getLogger(__name__)

REQUIRED_CONFIG = ["KEEPASSDB"]


def _get_config_var(var, config_dict):
    return config_dict.get(var)


def get_config(profile="default"):
    """
    Find database config from a config.ini file or relevant environment variables
    returns a KPConfig instance
    """
    config_file = Path(environ["HOME"]) / ".kp" / "config.ini"
    if config_file.exists():
        config = configparser.ConfigParser()
        config.read(config_file)
        logger.debug("Reading config from file")
        if profile not in config:
            raise typer.BadParameter(f"Profile {profile} does not exist")
        if config[profile]:
            config_location = config[profile]
    else:
        logger.debug("No config file found, reading config from environment")
        config_location = environ

    missing_config = [
        var for var in REQUIRED_CONFIG if _get_config_var(var, config_location) is None
    ]
    if missing_config:
        logger.error("Missing config variable(s): %s", ", ".join(missing_config))
        raise typer.Exit(1)
    db_config = KpConfig(
        filename=Path(_get_config_var("KEEPASSDB", config_location)),
        password=_get_config_var("KEEPASSDB_PASSWORD", config_location),
        keyfile=_get_config_var("KEEPASSDB_KEYFILE", config_location),
    )
    if not db_config.filename.exists():
        logger.error("Database file %s does not exist", db_config.filename)
        raise typer.Exit(1)
    typer.secho(f"Database: {db_config.filename}", fg=typer.colors.YELLOW)
    return db_config


def echo_banner(message: str, **style_options):
    """Helper function to print a banner style message"""
    banner = "=" * 80
    typer.secho(f"{banner}\n{message}\n{banner}", **style_options)
