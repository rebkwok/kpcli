#!/usr/bin/env python3
import attr
from pykeepass import PyKeePass
import pyperclip


class KpDatabaseConnector:
    """
    Connects to and interacts with a KeePassX database.
    """

    def __init__(self, db_config):
        self.db = PyKeePass(*attr.astuple(db_config))

    def list_group_names(self):
        return [group.name for group in self.db.groups]

    def list_group_entries(self, group_name):
        group = self.find_group(group_name=group_name)
        return [entry.title for entry in group.entries]

    def find_entries(self, query, group=None):
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
            return self.db.find_entries(title=query, group=group, recursive=False, regex=True, flags="i")
        else:
            return self.db.find_entries(title=query, regex=True, flags="i")

    def find_group(self, group_name):
        """Find the first matching group"""
        return self.db.find_groups(name=group_name, regex=True, flags="i", first=True)

    def add_new_entry(self, group, title, username, password, url, notes):
        self.db.add_entry(group, title, username, password, url=url, notes=notes)
        self.db.save()

    def change_password(self, entry, new_password):
        entry.password = new_password
        self.db.save()

    def copy_to_clipboard(self, entry, item):
        try:
            pyperclip.copy(getattr(entry, item))
        except AttributeError:
            raise AttributeError(f"Entry has no attribute {item}")

    def get_details(self, entry, show_password=False):
        return {
            "name": f"{entry.group.name}/{entry.title}",
            "username": entry.username,
            "password": entry.password if show_password else "*" * len(entry.password),
            "URL": entry.url or "",
            "Notes": entry.notes or ""
        }
