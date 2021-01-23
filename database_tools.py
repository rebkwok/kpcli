#!/usr/bin/env python3
import attr
from pykeepass import PyKeePass
import pyperclip


INVALID_ATTRIBUTE = "<invalid>"


class KpDatabaseConnector:
    
    def __init__(self, db_config):
        self.db = PyKeePass(db_config.path, password=db_config.password)

    def list_group_names(self):
        return [group.name for group in self.db.groups]

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

    def add_new_entry(self):
        group = None
        print("New entry:")
        while group is None:
            group_name = input("Group name (leave empty for Root group: ")
            group = self.db.find_groups(name=group_name, regex=True, flags="i", first=True)
            if group is None:
                print("No matching group found, please enter one of the following groups: {group_names}")
    
        title = None
        while not title:
            title = input("Title: ")
            if not title:
                print("Title is required")
            else:
                existing_entries = self.db.find_entries(title=title, group=group, recursive=False, regex=True, flags="i")
                if existing_entries:
                    print("An entry already exists for that group/title, please enter a different title.")
                    title = None
    
        username = input("Username: ")
        password = input("Password: ")
        url = input("Url: ")
        notes = input("Notes: ")
        self.db.add_entry(group, title, username, password, url=url, notes=notes)
        self.db.save()
        print("================================")
        print(f"New entry added:  {group.name}/{title}\nUsername {username}\nPassword {'*' * len(password)}\nURL: {url}\nNotes: {notes}")

    def change_password(self, entry, new_password):
        entry.password = new_password
        self.db.save()
        print(f"{entry.group.name}/{entry.title}: password updated")

    def copy_to_clipboard(self, entry, item):
        value = getattr(entry, "password", INVALID_ATTRIBUTE)
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
