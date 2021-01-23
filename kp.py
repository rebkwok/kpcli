#!/usr/bin/env python3
import argparse
import logging
from os import environ
from pathlib import Path

from compare_databases import KpDatabaseComparator
from datastructures import KpConfig
from database_tools import KpDatabaseConnector

logger = logging.getLogger(__name__)


def main(compare=False, get=None, add=False, list_groups=False, list_group_entries=False, new_password=None, show_password=False, show_details=False):
    missing_config = [var for var in ["KEEPASSDB", "KEEPASSDB_PASSWORD"] if environ.get(var) is None]
    if missing_config:
        logger.error("Missing environment variable(s): %s", ", ".join())
        return
    db_config = KpConfig(path=Path(environ["KEEPASSDB"]), password=environ["KEEPASSDB_PASSWORD"])
    if not db_config.path.exists():
        logger.error("Database file %s does not exist", db_config.path)
        return

    if compare:
        comparator = KpDatabaseComparator(db_config)
        comparator.compare_for_conflicts()
    else:
        connector = KpDatabaseConnector(db_config)
        if list_groups:
            group_names = "\n".join(connector.list_group_names())
            print(f"Groups:\n=======\n{group_names}")
        if list_group_entries:
            group = list_group_entries
            entry_names = "\n".join(connector.list_group_entries(group))
            print(f"Entries in group {group}:\n================================\n{entry_names}")
        if add:
            connector.add_new_entry()

        matching_entries = connector.find_entries(get)
        if new_password:
            if not get:
                logging.error("Specify an entry to update with -g")
                return
            if len(matching_entries) > 1:
                logging.error("Matched more than one entry, can't update password.")
                return
            if not matching_entries:
                logging.error("No entries found")
            entry = matching_entries[0]
            connector.change_password(entry, new_password)

        if get and not new_password:
            for entry in matching_entries:
                connector.get_details(entry, show_password=show_password)
                if len(matching_entries) == 1:
                    connector.copy_to_clipboard(matching_entries[0], "password")


if __name__ == "__main__":
    logging.basicConfig(level=environ.get("LOGLEVEL", "INFO"))
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
    parser.add_argument("--list-group-entries", type=str, help="List all entries in specified group")
    parser.add_argument("--show-password", action="store_true")
    parser.add_argument("--show-details", "-d", action="store_true")

    arguments = parser.parse_args()
    main(
        compare=arguments.compare,
        add=arguments.add,
        get=arguments.get,
        list_groups=arguments.list_groups,
        list_group_entries=arguments.list_group_entries,
        new_password=arguments.update_password,
        show_password=arguments.show_password,
        show_details=arguments.show_details
    )
