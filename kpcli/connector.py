#!/usr/bin/env python3
"""Connect to and interact with a KeePassX database."""

import attr
from pykeepass import PyKeePass
import pyperclip


class KpDatabaseConnector:
    """
    Connects to and interacts with a KeePassX database.
    """

    def __init__(self, db_config):
        self.db = PyKeePass(*attr.astuple(db_config))

    def add_group(self, group_name, super_group=None):
        if super_group is None:
            super_group = self.find_group("root")
        self.db.add_group(super_group, group_name)
        self.db.save()

    def delete_group(self, group):
        self.db.delete_group(group)
        self.db.save()

    def list_group_names(self):
        """Fetch names of all groups"""
        return sorted(
            [group.name for group in self.db.groups], key=lambda name: name.lower()
        )

    def list_group_entries(self, group_name):
        """Fetch names of all entries in a single group"""
        group = self.find_group(group_name=group_name)
        return sorted(
            [entry.title for entry in group.entries], key=lambda name: name.lower()
        )

    def find_entries(self, query, group=None):
        """
        Fetch entries from a query string, formatted optionally as <group>/<entry title>.
        Both <group> and <entry title> are case insensitive and can be partial terms.
        If a group is provided, entries will only be looked for in that group.
        """
        if query is None:
            return []
        if group is None:
            query = query.split("/")
            if len(query) > 1:
                group_name, query = query
                group = self.find_group(group_name=group_name)
            else:
                query = query[0]

        if group:
            # recursive=False because if we have a specific group we want to search this group only
            entries = self.db.find_entries(
                title=query, group=group, recursive=False, regex=True, flags="i"
            )
        else:
            entries = self.db.find_entries(title=query, regex=True, flags="i")
        entries.sort(key=lambda entry: (entry.group.name, entry.title))
        return entries

    def find_group(self, group_name):
        """Find the first matching group"""
        return self.db.find_groups(name=group_name, regex=True, flags="i", first=True)

    def add_new_entry(self, group, title, username, password, url, notes):
        """Add a new entry"""
        self.db.add_entry(group, title, username, password, url=url, notes=notes)
        self.db.save()

    def delete_entry(self, entry):
        """Delete an entry"""
        self.db.delete_entry(entry)
        self.db.save()

    def edit_entry(self, entry, field, new_value):
        """Edit a specified field on an entry"""
        try:
            # first check the field is a valid one
            getattr(entry, field)
        except AttributeError:
            raise AttributeError(f"Entry has no attribute {field}")
        setattr(entry, field, new_value)
        self.db.save()

    def change_password(self, entry, new_password):
        """Change an entry's password"""
        entry.password = new_password
        self.db.save()

    def copy_to_clipboard(self, entry, item):
        """Copy the requested item to the clipboard"""
        try:
            value = getattr(entry, item)
        except AttributeError:
            raise AttributeError(f"Entry has no attribute {item}")

        if value is not None:
            pyperclip.copy(getattr(entry, item))
        else:
            raise ValueError(f"{item} is None, nothing to copy")

    def get_details(self, entry, show_password=False):
        """Retrieve details for a single entry"""
        return {
            "name": f"{entry.group.name}/{entry.title}",
            "username": entry.username,
            "password": entry.password if show_password else "*" * len(entry.password),
            "URL": entry.url or "",
            "Notes": entry.notes or "",
        }
