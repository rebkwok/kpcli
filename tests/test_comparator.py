#!/usr/bin/env python3

from ..comparator import KpDatabaseComparator
from ..datastructures import KpConfig


def test_compare_no_conflicts(test_db_path):
    db_path = test_db_path("test_db")
    comparator = KpDatabaseComparator(KpConfig(filename=db_path, password="test"))
    assert comparator.get_conflicting_data() == comparator.generate_tables_of_conflicts() == {}


def test_compare(test_db_path):
    db_path = test_db_path("test_compare")
    comparator = KpDatabaseComparator(KpConfig(filename=db_path, password="test"))
    conflicts = comparator.get_conflicting_data()
    # 1 comparison database
    assert len(conflicts) == 1
    comparator_path = str(db_path.parent / "test_compare_conflicting.kdbx")
    missing_in_comparison, missing_in_main, conflicting_entries = conflicts[comparator_path]
    assert missing_in_comparison == set()
    assert missing_in_main == {'blue/test4'}
    assert conflicting_entries == {('red/test1', 'username, password'), ('blue/test3', 'username')}


def test_compare_with_details(test_db_path):
    db_path = test_db_path("test_compare")
    comparator = KpDatabaseComparator(KpConfig(filename=db_path, password="test"))
    conflicts = comparator.get_conflicting_data(show_details=True)
    comparator_path = str(db_path.parent / "test_compare_conflicting.kdbx")
    missing_in_comparison, missing_in_main, conflicting_entries = conflicts[comparator_path]
    assert missing_in_comparison == set()
    assert missing_in_main == {'blue/test4'}
    assert conflicting_entries == {
        ('red/test1', 'username: test1 vs redtest, password: test1 vs pass1'),
        ('blue/test3', 'username: test3 vs testblue')
    }
