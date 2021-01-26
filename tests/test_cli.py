#!/usr/bin/env python3
from os import environ
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from kpcli.kp import app

runner = CliRunner()


def get_env_vars(db_name, password="test", include_keyfile=False):
    env_vars = {
        # override HOME in case there is a config.ini file already on the host
       "HOME": str(Path(__file__).parent / f"fixtures"),
       "KEEPASSDB": str(Path(__file__).parent / f"fixtures/{db_name}.kdbx"),
       "KEEPASSDB_PASSWORD": password,
    }
    if include_keyfile:
        env_vars["KEEPASSDB_KEYFILE"] = str(Path(__file__).parent / f"fixtures/test_keyfile.key")
    return env_vars


@patch.dict(environ, get_env_vars("test_db"))
def test_list_groups():
    result = runner.invoke(app, ["ls"])
    assert result.exit_code == 0
    assert "MyGroup" in result.stdout


@patch.dict(environ, get_env_vars("test_db_with_keyfile", include_keyfile=True))
def test_database_with_keyfile():
    result = runner.invoke(app, ["ls"])
    assert result.exit_code == 0
    assert "MyKeyfileGroup" in result.stdout


@patch.dict(environ, get_env_vars("test_db", password="wrong"))
def test_invalid_credentials_database_with_keyfile():
    result = runner.invoke(app, ["ls"])
    assert result.exit_code == 1
    assert "Invalid credentials" in result.stdout
