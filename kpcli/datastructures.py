#!/usr/bin/env python3
from enum import Enum
from pathlib import Path

import attr
from pykeepass.group import Group
from typing import Optional

from kpcli.connector import KpDatabaseConnector


@attr.s
class KpContext:
    """
    A holder object so we can pass things around in the typer Context
    """

    connector = attr.ib(type=KpDatabaseConnector)
    group = attr.ib(type=Optional[Group], default=None)


@attr.s
class KpConfig:
    """
    KeePass database config
    """

    filename = attr.ib(type=Path)
    password = attr.ib(type=Optional[str], default=None)
    keyfile = attr.ib(type=Optional[str], default=None)


@attr.s
class KpEntry:
    """
    Datastructure to hold information about a single KeePass entry
    """

    title = attr.ib(type=str)
    username = attr.ib(type=str)
    password = attr.ib(type=str)
    group = attr.ib(type=str)
    url = attr.ib(type=str)
    notes = attr.ib(type=str)

    @classmethod
    def from_pykeepass_entry(cls, entry_obj):
        return cls(
            title=entry_obj.title,
            username=entry_obj.username,
            password=entry_obj.password,
            group=entry_obj.group.name,
            url=entry_obj.url,
            notes=entry_obj.notes,
        )

    @classmethod
    def from_tuple(cls, title, username, password, group, url, notes):
        return cls(
            title=title,
            username=username,
            password=password,
            group=group,
            url=url,
            notes=notes,
        )


class CopyOption(str, Enum):
    username = "username"
    u = "u"
    password = "password"
    p = "p"
    url = "url"
    notes = "notes"

    def __str__(self):
        if self.value == "u":
            return "username"
        elif self.value == "p":
            return "password"
        return self.value


class EditOption(str, Enum):
    username = "username"
    u = "u"
    url = "url"
    notes = "notes"

    def __str__(self):
        if self.value == "u":
            return "username"
        return self.value
