#!/usr/bin/env python3
import attr
from pykeepass import PyKeePass
import tableformatter
from tableformatter import generate_table

from datastructures import KpEntry


class KpDatabaseComparator:

    def __init__(self, db_config):
        self.config = db_config
        self.db = PyKeePass(self.config.path, password=self.config.password)

    def compare_tables(self, base_entries, comparison_db, show_conflicts=True):
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

    def compare_for_conflicts(self):
        db_name = self.config.path.stem
        dbfiles = list(self.config.path.parent.glob(f"{db_name}*.kdbx"))
        conflicts = len(dbfiles) > 1
        # find conflicting copies
        if conflicts:
            dbfilenames = "\n".join(dbfile.name for dbfile in dbfiles)
            print(f"Conflicting files found:\n{dbfilenames}")
        else:
            print(f"No conflicting files for {dbfiles[0].name}")

        if conflicts:
            main_db_entries = [KpEntry.parse(entry) for entry in self.db.entries]
            main_db_tuples = set(attr.astuple(entry) for entry in main_db_entries)
            conflicting_dbs = {
                dbfile.name: PyKeePass(dbfile, password=self.config.password) for dbfile in dbfiles if dbfile != self.config.path
            }
            for conflicting_db_name, conflicting_db in conflicting_dbs.items():
                print(f"=========Comparing {conflicting_db_name}========")
                conflicting_db_entries = [KpEntry.parse(entry) for entry in conflicting_db.entries]
                conflicting_db_tuples = set(attr.astuple(entry) for entry in conflicting_db_entries)

                in_main = main_db_tuples - conflicting_db_tuples
                in_main_entries = [KpEntry.from_tuple(*entry_tuple) for entry_tuple in in_main]
                in_conflicting = conflicting_db_tuples - main_db_tuples
                in_conflicting_entries = [KpEntry.from_tuple(*entry_tuple) for entry_tuple in in_conflicting]

                missing_in_comparison, _ = self.compare_tables(in_main_entries, conflicting_db, show_conflicts=False)
                missing_in_main, conflicts = self.compare_tables(in_conflicting_entries, self.db)
                column_headers = ["Main", "Comparison", "Conflicting fields"]
                rows = [
                    *[(f"{entry.group}/{entry.title}", "-", "") for entry in missing_in_comparison],
                    *[("-", f"{entry.group}/{entry.title}", "") for entry in missing_in_main],
                    *[(f"{entry.group}/{entry.title}", f"{entry.group}/{entry.title}", ",".join(attributes)) for entry, attributes in conflicts]
                ]
                print(generate_table(rows, column_headers, grid_style=tableformatter.FancyGrid()))
