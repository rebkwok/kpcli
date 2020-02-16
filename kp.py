#!/usr/bin/env python3.8
import argparse
import attr
import logging
from os import environ, path
from pathlib import Path

import pyperclip
from pykeepass import PyKeePass
import tableformatter
from tableformatter import generate_table

logger = logging.getLogger()
logger.setLevel("INFO")


@attr.s
class KpEntry:
    title = attr.ib(type=str)
    username = attr.ib(type=str)
    password = attr.ib(type=str)
    group = attr.ib(type=str)
    url = attr.ib(type=str)
    notes = attr.ib(type=str)

    @classmethod
    def parse(cls, entry_obj):
        return cls(
            title=entry_obj.title,
            username=entry_obj.username,
            password=entry_obj.password,
            group=entry_obj.group.name,
            url=entry_obj.url,
            notes=entry_obj.notes
        )

    def as_tuple(self):
        return (self.title, self.username, self.password, self.group, self.url, self.notes)

    @classmethod
    def from_tuple(cls, title, username, password, group, url, notes):
        return cls(
            title=title,
            username=username,
            password=password,
            group=group,
            url=url,
            notes=notes
        )


def find_entries(db, search):
    search = search.split("/")
    if len(search) > 1:
        group, title = search
        group = db.find_groups(name=group, regex=True, flags="i", first=True)
        return db.find_entries(title=title, group=group, regex=True, flags="i")
    else:
        title = search[0]
        return db.find_entries(title=title, regex=True, flags="i")


def compare_tables(base_entries, comparison_db, show_conflicts=True):
    missing_in_comparison = []
    conflicts = []
    for entry in base_entries:
        group = comparison_db.find_groups(name=entry.group, first=True)
        matching = comparison_db.find_entries(title=entry.title, group=group)
        assert len(matching) <= 1
        if not matching:
            missing_in_comparison.append(entry)
        elif show_conflicts:
            matching = KpEntry.parse(matching[0])
            mismatched = [
                attr for attr in ["username", "password", "url", "group", "notes"]
                if getattr(matching, attr) != getattr(entry, attr)
                ]
            if mismatched:
                conflicts.append((entry, mismatched))
    return missing_in_comparison, conflicts


def compare_for_conflicts(core_db_path, main_db, db_password):
    coredb_minus_ext = path.splitext(core_db_path.name)[0]
    dbfiles = list(core_db_path.parent.glob(f"{coredb_minus_ext}*.kdbx"))
    conflicts = len(dbfiles) > 1
    # find conflicting copies
    if conflicts:
        dbfilenames = "\n".join(dbfile.name for dbfile in dbfiles)
        print(f"Conflicting files found:\n{dbfilenames}")
    else:
        print(f"No conflicting files for {dbfiles[0].name}")

    if conflicts:
        main_db_entries = [KpEntry.parse(entry) for entry in main_db.entries]
        main_db_tuples = set(entry.as_tuple() for entry in main_db_entries)
        conflicting_dbs = {
            dbfile.name: PyKeePass(dbfile, password=db_password) for dbfile in dbfiles if dbfile != core_db_path
        }
        for conflicting_db_name, conflicting_db in conflicting_dbs.items():
            print(f"=========Comparing {conflicting_db_name}========")
            conflicting_db_entries = [KpEntry.parse(entry) for entry in conflicting_db.entries]
            conflicting_db_tuples = set(entry.as_tuple() for entry in conflicting_db_entries)

            in_main = main_db_tuples - conflicting_db_tuples
            in_main_entries = [KpEntry.from_tuple(*entry_tuple) for entry_tuple in in_main]
            in_conflicting = conflicting_db_tuples - main_db_tuples
            in_conflicting_entries = [KpEntry.from_tuple(*entry_tuple) for entry_tuple in in_conflicting]

            missing_in_comparison, _ = compare_tables(in_main_entries, conflicting_db, show_conflicts=False)
            missing_in_main, conflicts = compare_tables(in_conflicting_entries, main_db)
            column_headers = ["Main", "Comparison", "Conflicting fields"]
            rows = [
                *[(f"{entry.group}/{entry.title}", "-", "") for entry in missing_in_comparison],
                *[("-", f"{entry.group}/{entry.title}", "") for entry in missing_in_main],
                *[(f"{entry.group}/{entry.title}", f"{entry.group}/{entry.title}", ",".join(attributes)) for entry, attributes in conflicts]
            ]
            print(generate_table(rows, column_headers, grid_style=tableformatter.FancyGrid()))


def add_new_entry(main_db, group_names):
    group = None
    print("New entry:")
    while group is None:
        group_name = input("Group name (leave empty for Root group: ")
        group = main_db.find_groups(name=group_name, regex=True, flags="i", first=True)
        if group is None:
            print("No matching group found, please enter one of the following groups: {group_names}")

    title = None
    while not title:
        title = input("Title: ")
        if not title:
            print("Title is required")
        else:
            existing_entries = main_db.find_entries(title=title, group=group, recursive=False, regex=True, flags="i")
            if existing_entries:
                print("An entry already exists for that group/title, please enter a different title.")
                title = None

    username = input("Username: ")
    password = input("Password: ")
    url = input("Url: ")
    notes = input("Notes: ")
    main_db.add_entry(group, title, username, password, url=url, notes=notes)
    main_db.save()
    print("================================")
    print(f"New entry added:  {group.name}/{title}\nUsername {username}\nPassword {'*' * len(password)}\nURL: {url}\nNotes: {notes}")

def main(compare=False, get=None, add=False, list_groups=False, new_password=None, show_password=False, show_details=False):
    db_path = environ.get("KEEPASSDB")
    password = environ.get("KEEPASSDB_PASSWORD")
    if not all([db_path, password]):
        logger.error(
            "Missing environment variable(s): %s",
            ", ".join([var for var in ["KEEPASSDB", "KEEPASSDB_PASSWORD"] if environ.get(var) is None])
        )
        return

    core_db_path = Path(db_path)
    if not core_db_path.exists():
        logger.error("Database file %s does not exist", core_db_path)
        return

    main_db = PyKeePass(core_db_path, password=password)

    group_names = "\n".join(f"- {group.name}" for group in main_db.groups)
    if list_groups:
        print(f"Groups:\n{group_names}")

    if add:
        add_new_entry(main_db, group_names)

    matching_entries = find_entries(main_db, get) if get else None
    if new_password and not get:
        logging.error("Specify an entry to update with -g")
        return

    if new_password:
        if len(matching_entries) > 1:
            logging.error("Matched more than one entry, can't update password.")
            return
        if not matching_entries:
            logging.error("No entries found")
        entry = matching_entries[0]
        entry.password = new_password
        main_db.save()
        print(f"{entry.group.name}/{entry.title}: password updated")

    if get and not new_password:
        for entry in matching_entries:
            print(f"==========={entry.group.name}/{entry.title}==========")
            if entry.username:
                print(f"Username: {entry.username}")
            if show_password:
                print(f"Password: {entry.password}")
            if show_details:
                print(f"URL: {entry.url or ''}")
                print(f"Notes: {entry.notes or ''}")

            if len(matching_entries) == 1:
                pyperclip.copy(entry.password)
                print(f"Password copied to clipboard")

    if compare:
        compare_for_conflicts(core_db_path, main_db, password)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Command line interface to a keepass database.\n"
                    "Set the required environment variables:\n"
                    "- KEEPASSDB (path to your keepass database file)\n- KEEPASSDB_PASSWORD"
    )
    parser.add_argument("--compare", "-c", action="store_true", help="Check for conflicting copies and report conflicts")
    parser.add_argument("--get", "-g", type=str, help="Get entry by title or group/title")
    parser.add_argument("--update-password", "-u", type=str, help="Update password; use with -g to select an entry to update")
    parser.add_argument("--add", "-a", action="store_true", help="Add new entry; prompts for entry info")
    parser.add_argument("--list-groups", action="store_true", help="List all groups")
    parser.add_argument("--show-password", action="store_true")
    parser.add_argument("--show-details", "-d", action="store_true")

    arguments = parser.parse_args()
    main(
        compare=arguments.compare,
        add=arguments.add,
        get=arguments.get,
        list_groups=arguments.list_groups,
        new_password=arguments.update_password,
        show_password=arguments.show_password,
        show_details=arguments.show_details
    )