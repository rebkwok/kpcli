#!/usr/bin/env python3
import argparse
import logging
from os import environ
from pathlib import Path

import pyperclip
from pykeepass import PyKeePass

from compare_databases import compare_for_conflicts
from database_tools import find_entries, add_new_entry


logger = logging.getLogger()
logger.setLevel("INFO")


def main(compare=False, get=None, add=False, list_groups=False, new_password=None, show_password=False, show_details=False):
    db_path = environ.get("KEEPASSDB")
    password = environ.get("KEEPASSDB_PASSWORD")
    if not all([db_path, password]):
        logger.error(
            "Missing environment variable(s): %s",
            ", ".join([var for var in ["KEEPASSDB", "KEEPASSDB_PASSWORD"] if environ.get(var) is None])
        )
        return

    db_path = Path(db_path)
    if not Path(db_path).exists():
        logger.error("Database file %s does not exist", db_path)
        return

    db = PyKeePass(db_path, password=password)

    group_names = "\n".join(f"- {group.name}" for group in db.groups)
    if list_groups:
        print(f"Groups:\n{group_names}")

    if add:
        add_new_entry(db)

    matching_entries = find_entries(db, get) if get else None
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
        db.save()
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
        compare_for_conflicts(db_path, db, password)


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
