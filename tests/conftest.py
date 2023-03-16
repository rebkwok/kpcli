#!/usr/bin/env python3
from pathlib import Path
import shutil

import pytest


GROUP_ENTRY_NAMES = ["Entry with no password", "Entry with no username", "gmail"]

@pytest.fixture
def temp_db_path():
    test_db = Path(__file__).parent / "fixtures/test_db.kdbx"
    temp_db = Path(__file__).parent / "fixtures/temp_db.kdbx"
    shutil.copy(test_db, temp_db)
    yield temp_db
    temp_db.unlink()


@pytest.fixture
def test_db_path():
    def named_test_db_path(db_name):
        return Path(__file__).parent / f"fixtures/{db_name}.kdbx"

    yield named_test_db_path


@pytest.fixture
def mock_config_file():
    # HOME is set to the fixtures file in tests
    temp_config_path = Path(__file__).parent / "fixtures/.kp"
    temp_config_path.mkdir(parents=True, exist_ok=True)
    temp_config_file = temp_config_path / "config.ini"

    db_path = Path(__file__).parent / f"fixtures/test_db.kdbx"
    with open(temp_config_file, "w") as outfile:
        outfile.write(
            f"""
            [default]
            KEEPASSDB={str(db_path)}
            KEEPASSDB_PASSWORD=badpass
            
            [test]
            KEEPASSDB={str(db_path)}
            KEEPASSDB_PASSWORD=test
            """
        )
    yield
    temp_config_file.unlink()
    temp_config_path.rmdir()
