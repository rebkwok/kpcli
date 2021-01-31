#!/usr/bin/env python3
from os import environ
from pathlib import Path
from unittest.mock import call, patch

import pytest
from typer.testing import CliRunner

from kpcli.cli import app

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


@patch.dict(environ, get_env_vars("test_db"))
def test_list_groups_with_entries():
    result = runner.invoke(app, ["ls", "--entries"])
    assert result.exit_code == 0
    for group_name in ["Root", "MyGroup"]:
        assert group_name in result.stdout
    for entry_name in ["Test Root Entry", "gmail"]:
        assert entry_name in result.stdout


@patch.dict(environ, get_env_vars("test_db"))
def test_list_single_group_with_entries():
    result = runner.invoke(app, ["ls", "-g", "mygr", "--entries"])
    assert result.exit_code == 0
    for name in ["MyGroup", "gmail"]:
        assert name in result.stdout
    for name in ["Root", "Test Root Entry"]:
        assert name not in result.stdout


@patch.dict(environ, get_env_vars("test_db"))
def test_list_single_group_invalid_name():
    result = runner.invoke(app, ["ls", "-g", "foo"])
    assert result.exit_code == 1
    assert "No group matching 'foo' found" in result.stdout


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


@pytest.mark.parametrize(
    "command,expected_args",
    [
        (
            ["cp", "gmail"],
            ["testpass", ""],
        ),  # copies password by default, then copies empty string
        (["cp", "gmail", "username"], ["test@test.com"]),  # copy username
        (["cp", "gmail", "u"], ["test@test.com"]),  # copy username with abbreviation
    ],
)
@patch.dict(environ, get_env_vars("test_db"))
@patch("kpcli.connector.pyperclip.copy")
@patch("kpcli.cli.typer.prompt")
@patch("kpcli.cli.signal.alarm")
def test_copy(mock_alarm, mock_prompt, mock_copy, command, expected_args):
    # mock prompt for confirmation after password copy - this will trigger the clipboard to be cleared
    # also mock the alarm signal so it doesn't pollute other tests
    mock_prompt.return_value = "y"
    runner.invoke(app, command)
    calls = [call(arg) for arg in expected_args]
    mock_copy.assert_has_calls(calls)


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
def test_add_with_missing_group(temp_db_path):
    result = runner.invoke(app, ["get", "test entry"])
    assert "No matching entry found" in result.stdout
    result = runner.invoke(
        app,
        [
            "add",
            "--title",
            "a test entry",
            "--username",
            "Bugs Bunny",
            "--password",
            "carrot",
        ],
    )
    assert result.exit_code == 1
    assert "--group is required" in result.stdout


@patch.dict(environ, get_env_vars("temp_db"))
def test_add_with_existing_entry_title(temp_db_path):
    result = runner.invoke(app, ["get", "mygroup/gmail"])
    assert "gmail" in result.stdout
    result = runner.invoke(
        app,
        [
            "add",
            "--group",
            "mygroup",
            "--title",
            "gmail",
            "--username",
            "Bugs Bunny",
            "--password",
            "carrot",
        ],
    )
    assert "An entry already exists for 'gmail' in group MyGroup" in result.stdout


@patch.dict(environ, get_env_vars("temp_db"))
def test_change_password(temp_db_path):
    result = runner.invoke(app, ["get", "gmail", "--show-password"])
    assert "testpass" in result.stdout
    runner.invoke(app, ["change-password", "gmail", "--password", "boop"])
    result = runner.invoke(app, ["get", "gmail", "--show-password"])
    assert "testpass" not in result.stdout
    assert "boop" in result.stdout
