#!/usr/bin/env python3
from os import environ

import pytest
from unittest.mock import patch

from kpcli.connector import KpDatabaseConnector
from kpcli.datastructures import KpConfig


def test_list_all_groups(test_db_path):
    db_path = test_db_path("test_db")
    connector = KpDatabaseConnector(KpConfig(filename=db_path, password="test"))
    assert connector.list_group_names() == ["Root", "MyGroup"]


@pytest.mark.parametrize("query", ("MyGroup", "group", "mygroup", "my"))
def test_list_group_entries(test_db_path, query):
    """Test fetching group entries with full or partial group name"""
    db_path = test_db_path("test_db")
    connector = KpDatabaseConnector(KpConfig(filename=db_path, password="test"))
    assert connector.list_group_entries(query) == ["gmail"]


@pytest.mark.parametrize(
    "query,expected_number", [("gm", 1), ("gmail", 1), ("il", 1), ("foo", 0)]
)
def test_find_entries(test_db_path, query, expected_number):
    db_path = test_db_path("test_db")
    connector = KpDatabaseConnector(KpConfig(filename=db_path, password="test"))
    entries = connector.find_entries(query)
    assert len(entries) == expected_number
    if expected_number == 1:
        assert entries[0].title == "gmail"


@pytest.mark.parametrize(
    "query,group_name,expected_number",
    [("gm", "mygroup", 1), ("gmail", "mygroup", 1), ("gmail", "root", 0)],
)
def test_find_entries_with_group(test_db_path, query, group_name, expected_number):
    db_path = test_db_path("test_db")
    connector = KpDatabaseConnector(KpConfig(filename=db_path, password="test"))
    group = connector.find_group(group_name)
    entries = connector.find_entries(query, group)
    assert len(entries) == expected_number
    if expected_number == 1:
        assert entries[0].title == "gmail"


@pytest.mark.parametrize(
    "show_password,password", [(False, "********"), (True, "testpass")]
)
def test_get_details(test_db_path, show_password, password):
    db_path = test_db_path("test_db")
    connector = KpDatabaseConnector(KpConfig(filename=db_path, password="test"))
    entry = connector.find_entries("gmail")[0]
    assert connector.get_details(entry, show_password) == {
        "name": "MyGroup/gmail",
        "username": "test@test.com",
        "password": password,
        "URL": "gmail.com",
        "Notes": "",
    }


@pytest.mark.parametrize(
    "attribute,expected",
    [("username", "test@test.com"), ("password", "testpass"), ("url", "gmail.com")],
)
@patch("kpcli.connector.pyperclip.copy")
def test_copy(mock_copy, test_db_path, attribute, expected):
    db_path = test_db_path("test_db")
    connector = KpDatabaseConnector(KpConfig(filename=db_path, password="test"))
    entry = connector.find_entries("gmail")[0]
    connector.copy_to_clipboard(entry, attribute)
    mock_copy.assert_called_with(expected)


def test_copy_invalid_attribute(test_db_path):
    db_path = test_db_path("test_db")
    connector = KpDatabaseConnector(KpConfig(filename=db_path, password="test"))
    entry = connector.find_entries("gmail")[0]
    with pytest.raises(AttributeError):
        connector.copy_to_clipboard(entry, "foo")


def test_change_password(temp_db_path):
    connector = KpDatabaseConnector(KpConfig(filename=temp_db_path, password="test"))
    entry = connector.find_entries("gmail")[0]
    connector.change_password(entry, "new_pass")
    assert connector.get_details(entry, show_password=True)["password"] == "new_pass"


def test_add_new(temp_db_path):
    connector = KpDatabaseConnector(KpConfig(filename=temp_db_path, password="test"))
    group = connector.find_group("root")
    connector.add_new_entry(group, "A new entry", "test user", "pass", "", "")
    entry = connector.find_entries("new")[0]
    assert connector.get_details(entry)["name"] == "Root/A new entry"


def test_edit_entry(temp_db_path):
    connector = KpDatabaseConnector(KpConfig(filename=temp_db_path, password="test"))
    entry = connector.find_entries("gmail")[0]
    connector.edit_entry(entry, "username", "anewemail@test.com")
    assert (
        connector.get_details(entry, show_password=True)["username"]
        == "anewemail@test.com"
    )

    connector.edit_entry(entry, "url", "http://hey-a-new-url.com")
    assert (
        connector.get_details(entry, show_password=True)["URL"]
        == "http://hey-a-new-url.com"
    )


def test_delete_entry(temp_db_path):
    connector = KpDatabaseConnector(KpConfig(filename=temp_db_path, password="test"))
    entry = connector.find_entries("gmail")[0]
    connector.delete_entry(entry)
    assert connector.find_entries("gmail") == []


def test_add_group(temp_db_path):
    connector = KpDatabaseConnector(KpConfig(filename=temp_db_path, password="test"))
    connector.add_group("a new group")
    assert "a new group" in connector.list_group_names()


def test_delete_group(temp_db_path):
    connector = KpDatabaseConnector(KpConfig(filename=temp_db_path, password="test"))
    assert connector.list_group_names() == ["Root", "MyGroup"]
    group = connector.find_group("MyGroup")
    connector.delete_group(group)
    assert connector.list_group_names() == ["Root"]
