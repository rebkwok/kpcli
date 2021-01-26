#!/usr/bin/env python3
"""Compares two or more KeePassX databases for conflicting entries"""

# standards
import attr
from typing import Set

# third parties
from pykeepass import PyKeePass
from pykeepass.exceptions import CredentialsError
import tableformatter
from tableformatter import generate_table

from kpcli.datastructures import KpEntry


class KpDatabaseComparator:
    """
    Compares a main KeePassX database with potentially conflicting versions.
    """

    entry_fields = ["username", "password", "url", "group", "notes"]

    def __init__(self, db_config):
        self.config = db_config
        self.db = PyKeePass(*attr.astuple(db_config))

    def _get_matching_entry(self, db, entry):
        """Find matching entry from specific database by entry group and title"""
        group = db.find_groups(name=entry.group, first=True)
        return db.find_entries(title=entry.title, group=group, first=True)

    def compare_database_entries(
        self,
        differences: Set[tuple],
        comparison_db: PyKeePass,
        show_details: bool = False,
    ):
        """
        Take a set of entries-as-tuple that are known to differ in a comparison database and identify
        which are missing, and which field have conflicts
        """
        missing_in_comparison = set()
        missing_in_main = set()
        conflicts = set()

        def _format_conflict(conflict):
            if show_details:
                return f"{conflict[0]}: {conflict[1]} vs {conflict[2]}"
            return conflict[0]

        for entry_tuple in differences:
            entry = KpEntry.from_tuple(*entry_tuple)
            main = self._get_matching_entry(self.db, entry)
            comparison = self._get_matching_entry(comparison_db, entry)
            if main and comparison:
                # find conflicts in the entry fields we care about
                mismatched_items = []
                for field in self.entry_fields:
                    main_value = getattr(main, field)
                    comparison_value = getattr(comparison, field)
                    if main_value != comparison_value:
                        mismatched_items.append((field, main_value, comparison_value))
                conflicts.add(
                    (
                        f"{entry.group}/{entry.title}",
                        ", ".join(
                            [_format_conflict(item) for item in mismatched_items]
                        ),
                    )
                )
            elif not comparison:
                missing_in_comparison.add(f"{entry.group}/{entry.title}")
            elif not main:
                missing_in_main.add(f"{entry.group}/{entry.title}")
        return missing_in_comparison, missing_in_main, conflicts

    def get_conflicting_data(self, show_details=False):
        """
        Find databases with the same filepath stem as the main database and compares them for missing and
        conflicting entries.
        Returns a dict of database filenames and their conflicts with the main database as a tuple of
        (
            {entries present in main, missing in comparison db},
            {entries present in comparison, missing in main db},
            {conflicting entries}
        )
        e.g
        (
            {"group1/title1"},
            {"group1/title2", "group2/title3"},
            {
                ("group3/title3", "username"),
                ("group4/title4", "password")
        )
        """
        db_name = self.config.filename.stem
        # find conflicting copies
        comparison_db_files = set(
            self.config.filename.parent.glob(f"{db_name}*.kdbx")
        ) - {self.config.filename}
        conflicting_data = {}
        main_entries = set(
            attr.astuple(KpEntry.from_pykeepass_entry(entry))
            for entry in self.db.entries
        )
        for comparison_db_file in comparison_db_files:
            try:
                comparison_db = PyKeePass(
                    comparison_db_file, password=self.config.password
                )
            except CredentialsError:
                # Conflicting copies will have the same credentials as the original, but another db with the same stem
                # may exist. In that case, just report None
                conflicting_entries = None
            else:
                comparison_entries = set(
                    attr.astuple(KpEntry.from_pykeepass_entry(entry))
                    for entry in comparison_db.entries
                )
                # Find the entries that are not identical in the comparison db.
                differing_entries = main_entries ^ comparison_entries
                # Identify the differences
                conflicting_entries = self.compare_database_entries(
                    differing_entries, comparison_db, show_details=show_details
                )
            conflicting_data[str(comparison_db_file)] = conflicting_entries
        return conflicting_data

    def generate_tables_of_conflicts(self, show_details=False):
        """
        Find databases with the same filepath stem as the main database and compare them for missing and
        conflicting entries.
        Returns a dict of tabulated results for each conflicting database found which can be passed to `print` or `typer.echo`.
        """
        conflicting_tables = {}
        for comparison_db_filename, data in self.get_conflicting_data(
            show_details
        ).items():
            if data is None:
                conflicting_tables[
                    comparison_db_filename
                ] = "Database could not be accessed"
                continue
            missing_in_comparison, missing_in_main, conflicts = data
            # Build a table of conflicts
            if not any([missing_in_comparison, missing_in_main, conflicts]):
                conflicting_tables[comparison_db_filename] = "No conflicts found"
            else:
                column_headers = ["Main", "Conflicting", "Conflicting fields"]
                rows = [
                    *[(entry_name, "-", "") for entry_name in missing_in_comparison],
                    *[("-", entry_name, "") for entry_name in missing_in_main],
                    *[
                        (entry_name, entry_name, conflicting_fields)
                        for entry_name, conflicting_fields in conflicts
                    ],
                ]
                conflicting_tables[comparison_db_filename] = generate_table(
                    rows, column_headers, grid_style=tableformatter.FancyGrid()
                )
        return conflicting_tables
