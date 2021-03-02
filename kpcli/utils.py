#!/usr/bin/env python3
# standards
import configparser
import logging
from os import environ
from pathlib import Path

import typer

from kpcli.datastructures import Encrypter, KpConfig


logger = logging.getLogger(__name__)

REQUIRED_CONFIG = ["KEEPASSDB"]


def get_config_from_file(profile="default"):
    """
    Identify config location
    Returns a config parser or environ
    """
    config_file = Path(environ["HOME"]) / ".kp" / "config.ini"
    if config_file.exists():
        config = configparser.ConfigParser()
        config.read(config_file)
        logger.debug("Reading config from file")
        if profile not in config:
            raise typer.BadParameter(f"Profile {profile} does not exist")
        if config[profile]:
            return config[profile]


def get_config(profile="default"):
    """
    Find database config from a config.ini file or relevant environment variables
    returns a KPConfig instance
    """
    config_from_file = get_config_from_file(profile) or {}
    db_path = environ.get("KEEPASSDB") or config_from_file.get("KEEPASSDB")
    password = environ.get("KEEPASSDB_PASSWORD") or config_from_file.get(
        "KEEPASSDB_PASSWORD"
    )
    keyfile = environ.get("KEEPASSDB_KEYFILE") or config_from_file.get(
        "KEEPASSDB_KEYFILE"
    )

    if db_path is None:
        logger.error("Missing config variable: KEEPASSDB")
        raise typer.Exit(1)

    db_config = KpConfig(
        filename=Path(db_path),
        password=password,
        keyfile=keyfile,
    )
    store_encrypted_password = environ.get(
        "STORE_ENCRYPTED_PASSWORD", config_from_file.get("STORE_ENCRYPTED_PASSWORD", False),
    )
    store_encrypted_password = str(store_encrypted_password).lower() in ["true", "1"]
    if not db_config.filename.exists():
        logger.error("Database file %s does not exist", db_config.filename)
        raise typer.Exit(1)
    if db_config.password is None and store_encrypted_password:
        encrypter = Encrypter()
        reset_password = environ.get("RESET_STORED_PASSWORD", False)
        reset_password = str(reset_password).lower() in ["true", "1"]
        if reset_password:
            encrypter.reset()
        else:
            db_config.password = encrypter.get_password()
    typer.secho(f"Database: {db_config.filename}", fg=typer.colors.YELLOW)
    return db_config, store_encrypted_password


def get_timeout(profile="default"):
    config_from_file = get_config_from_file(profile) or {}

    try:
        return int(
            environ.get("KEEPASSDB_TIMEOUT")
            or config_from_file.get("KEEPASSDB_TIMEOUT", 5)
        )
    except ValueError:
        typer.secho(
            "Invalid timeout found, defaulting to 5 seconds",
            fg=typer.colors.RED,
            bold=True,
        )
        return 5


def echo_banner(message: str, **style_options):
    """Helper function to print a banner style message"""
    banner = "=" * 80
    typer.secho(f"{banner}\n{message}\n{banner}", **style_options)


class InputTimedOut(Exception):
    pass


def inputTimeOutHandler(signum, frame):
    raise InputTimedOut
