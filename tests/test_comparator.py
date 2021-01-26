#!/usr/bin/env python3

from kpcli.comparator import KpDatabaseComparator
from kpcli.datastructures import KpConfig


def test_compare_no_conflicts(test_db_path):
    db_path = test_db_path("test_db1")
    comparator = KpDatabaseComparator(KpConfig(filename=db_path, password="test"))
    assert (
        comparator.get_conflicting_data()
        == comparator.generate_tables_of_conflicts()
        == {}
    )


def test_compare(test_db_path):
    db_path = test_db_path("test_compare")
    comparator = KpDatabaseComparator(KpConfig(filename=db_path, password="test"))
    conflicts = comparator.get_conflicting_data()
    # 1 comparison database
    assert len(conflicts) == 1
    comparator_path = str(db_path.parent / "test_compare_conflicting.kdbx")
    missing_in_comparison, missing_in_main, conflicting_entries = conflicts[
        comparator_path
    ]
    assert missing_in_comparison == set()
    assert missing_in_main == {"blue/test4"}
    assert conflicting_entries == {
        ("red/test1", "username, password"),
        ("blue/test3", "username"),
    }


def test_compare_with_details(test_db_path):
    db_path = test_db_path("test_compare")
    comparator = KpDatabaseComparator(KpConfig(filename=db_path, password="test"))
    conflicts = comparator.get_conflicting_data(show_details=True)
    comparator_path = str(db_path.parent / "test_compare_conflicting.kdbx")
    missing_in_comparison, missing_in_main, conflicting_entries = conflicts[
        comparator_path
    ]
    assert missing_in_comparison == set()
    assert missing_in_main == {"blue/test4"}
    assert conflicting_entries == {
        ("red/test1", "username: test1 vs redtest, password: test1 vs pass1"),
        ("blue/test3", "username: test3 vs testblue"),
    }


def test_compare_with_inaccessible_database(test_db_path):
    db_path = test_db_path("test_db")
    # the test db test_db_with_keyfile.kdbx has the same root filename as the test "main" file, but it
    # can't be opened with the same credentials
    comparator = KpDatabaseComparator(KpConfig(filename=db_path, password="test"))
    conflicts = comparator.get_conflicting_data()
    comparator_path = str(db_path.parent / "test_db_with_keyfile.kdbx")
    assert conflicts[comparator_path] is None
