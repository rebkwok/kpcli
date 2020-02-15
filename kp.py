#!/usr/bin/env python3.8
import argparse
import attr
import logging
from os import environ, path
from pathlib import Path

from pykeepass import PyKeePass

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


def compare(base_entries, comparison_db, base_name, comparison_name, show_conflicts=True):
    for entry in base_entries:
        group = comparison_db.find_groups(name=entry.group, first=True)
        matching = comparison_db.find_entries(title=entry.title, group=group)
        assert len(matching) <= 1
        if not matching:
            print(f"{entry.title} in {base_name} missing in {comparison_name} db")
        elif show_conflicts:
            matching = KpEntry.parse(matching[0])
            mismatched = [
                attr for attr in ["username", "password", "url", "group", "notes"]
                if getattr(matching, attr) != getattr(entry, attr)
                ]
            if mismatched:
                print(f"{entry.title} in {base_name} conflicts on {', '.join(mismatched)}")


def main(analyse, get=None, new_password=None):
    db_path = environ.get("KEEPASSDB")
    password = environ.get("KEEPASSDB_PASSWORD")
    if not all([db_path, password]):
        logger.error("You must set the KEEPASSDB and KEEPASSDB_PASSWORD variables")
        return

    core_db_path = Path(db_path)
    if not core_db_path.exists():
        logger.error("Database file %s does not exist", core_db_path)
        return

    main_db = PyKeePass(core_db_path, password=password)

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
                print(f"{entry.username}")
            print(f"{entry.password}")

    if analyse:
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
                dbfile.name: PyKeePass(dbfile, password=password) for dbfile in dbfiles if dbfile != core_db_path
            }
            for conflicting_db_name, conflicting_db in conflicting_dbs.items():
                print(f"=========Comparing {conflicting_db_name}========")
                conflicting_db_entries = [KpEntry.parse(entry) for entry in conflicting_db.entries]
                conflicting_db_tuples = set(entry.as_tuple() for entry in conflicting_db_entries)

                in_main = main_db_tuples - conflicting_db_tuples
                in_main_entries = [KpEntry.from_tuple(*entry_tuple) for entry_tuple in in_main]
                in_conflicting = conflicting_db_tuples - main_db_tuples
                in_conflicting_entries = [KpEntry.from_tuple(*entry_tuple) for entry_tuple in in_conflicting]

                compare(in_main_entries, conflicting_db, "main", "conflicting", show_conflicts=False)
                compare(in_conflicting_entries, main_db, "conflicting", "main")
                print("=========Done========")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--analyse", "-a", action="store_true", help="Check for conflicting copies and report conflicts")
    parser.add_argument("--get", "-g", type=str, help="Get entry by title or group/title")
    parser.add_argument("--update-password", "-u", type=str, help="Update password; use with -g to select an entry to update")

    arguments = parser.parse_args()
    main(arguments.analyse, get=arguments.get, new_password=arguments.update_password)