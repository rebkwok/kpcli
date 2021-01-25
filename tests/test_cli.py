#!/usr/bin/env python3
from os import environ
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from ..kp import app

runner = CliRunner()


def get_env_vars(db_name):
    return {
        # override HOME in case there is a config.ini file already on the host
       "HOME": str(Path(__file__).parent / f"fixtures"),
       "KEEPASSDB": str(Path(__file__).parent / f"fixtures/{db_name}.kdbx"),
       "KEEPASSDB_PASSWORD": "test"
   }


@patch.dict(environ, get_env_vars("test_db"))
def test_app_lists_groups():
    result = runner.invoke(app, ["ls"])
    assert result.exit_code == 0
    assert "MyGroup" in result.stdout
