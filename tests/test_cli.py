#!/usr/bin/env python3
from os import environ
from pathlib import Path
from unittest.mock import patch

import pyperclip
import pytest
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
        env_vars["KEEPASSDB_KEYFILE"] = str(
            Path(__file__).parent / f"fixtures/test_keyfile.key"
        )
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


@patch.dict(environ, get_env_vars("test_db"))
def test_config_file_overrides_env_vars(mock_config_file):
    # The config file has invalid credentials in the default profile
    result = runner.invoke(app, ["ls"])
    assert result.exit_code == 1
    assert "Invalid credentials" in result.stdout

    # valid credentials in the test profile
    result = runner.invoke(app, ["--profile", "test", "ls"])
    assert result.exit_code == 0


@patch.dict(environ, get_env_vars("test_db"))
def test_get():
    result = runner.invoke(app, ["get", "gmail"])
    assert result.exit_code == 0
    assert "MyGroup/gmail" in result.stdout


@patch.dict(environ, get_env_vars("test_db"))
def test_get_with_password():
    result = runner.invoke(app, ["get", "gmail"])
    assert "testpass" not in result.stdout
    assert "********" in result.stdout

    result = runner.invoke(app, ["get", "gmail", "--show-password"])
    assert "testpass" in result.stdout
    assert "********" not in result.stdout


@pytest.mark.skipif(environ.get("CI", "0") == "1", reason="skip if running as github action")
@patch.dict(environ, get_env_vars("test_db"))
def test_copy():
    # copies password by default
    runner.invoke(app, ["cp", "gmail"])
    assert pyperclip.paste() == "testpass"

    # copy username
    runner.invoke(app, ["cp", "gmail", "username"])
    assert pyperclip.paste() == "test@test.com"

    # copy username with abbreviation
    runner.invoke(app, ["cp", "gmail", "u"])
    assert pyperclip.paste() == "test@test.com"


@patch.dict(environ, get_env_vars("temp_db"))
def test_add(temp_db_path):
    result = runner.invoke(app, ["get", "test entry"])
    assert "No matching entry found" in result.stdout
    runner.invoke(
        app,
        [
            "add",
            "--group",
            "mygroup",
            "--title",
            "a test entry",
            "--username",
            "Bugs Bunny",
            "--password",
            "carrot",
        ],
    )
    result = runner.invoke(app, ["get", "test entry"])
    assert "MyGroup/a test entry" in result.stdout


@patch.dict(environ, get_env_vars("temp_db"))
def test_change_password(temp_db_path):
    result = runner.invoke(app, ["get", "gmail", "--show-password"])
    assert "testpass" in result.stdout
    runner.invoke(app, ["change-password", "gmail", "--password", "boop"])
    result = runner.invoke(app, ["get", "gmail", "--show-password"])
    assert "testpass" not in result.stdout
    assert "boop" in result.stdout
