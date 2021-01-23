#!/usr/bin/env python3
import attr
from pykeepass import PyKeePass
import pyperclip


INVALID_ATTRIBUTE = "<invalid>"


class KpDatabaseConnector:
    
    def __init__(self, db_config):
        self.db = PyKeePass(**db_config.asdict())

    def list_group_names(self):
        return [group.name for group in self.db.groups]

    def list_group_entries(self, group):
        group = self.db.find_groups(name=group, regex=True, flags="i", first=True)
        return [entry.title for entry in group.entries]

    def find_entries(self, search):
        if search is None:
            return []
        search = search.split("/")
        if len(search) > 1:
            group, title = search
            group = self.db.find_groups(name=group, regex=True, flags="i", first=True)
            return self.db.find_entries(title=title, group=group, regex=True, flags="i")
        else:
            title = search[0]
            return self.db.find_entries(title=title, regex=True, flags="i")

    def find_group(self, group_name):
        return self.db.find_groups(name=group_name, regex=True, flags="i", first=True)

    def find_entries_by_title(self, title, group):
        return self.db.find_entries(title=title, group=group, recursive=False, regex=True, flags="i")

    def add_new_entry(self, group, title, username, password, url, notes):
        self.db.add_entry(group, title, username, password, url=url, notes=notes)
        self.db.save()

    def change_password(self, entry, new_password):
        entry.password = new_password
        self.db.save()
        print(f"{entry.group.name}/{entry.title}: password updated")

    def copy_to_clipboard(self, entry, item):
        value = getattr(entry, item, INVALID_ATTRIBUTE)
        if value == INVALID_ATTRIBUTE:
            raise AttributeError(f"Entry has no attribute {item}")
        pyperclip.copy(value)
        print(f"{item} copied to clipboard")

    def get_details(self, entry, show_password=False):
        print(f"==========={entry.group.name}/{entry.title}==========")
        print(f"Username: {entry.username}")
        if show_password:
            print(f"Password: {entry.password}")
        print(f"URL: {entry.url or ''}")
        print(f"Notes: {entry.notes or ''}")
