#!/usr/bin/env python3
from pathlib import Path
import shutil

import pytest


@pytest.fixture
def temp_db_path():
    test_db = Path(__file__).parent / 'fixtures/test_db.kdbx'
    temp_db = Path(__file__).parent / 'fixtures/temp_db.kdbx'
    shutil.copy(test_db, temp_db)
    yield temp_db
    temp_db.unlink()


@pytest.fixture
def test_db_path():
    def named_test_db_path(db_name):
        return Path(__file__).parent / f'fixtures/{db_name}.kdbx'
    yield named_test_db_path
