#!/usr/bin/env python3
from datetime import datetime
from enum import Enum
from os import environ
from pathlib import Path
import random
import string

import attr
from cryptography.fernet import Fernet
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
    paste_timeout = attr.ib(type=int, default=5)


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


class Encrypter:
    """
    Helper class for storing and retrieving encrypted database password
    Generates an encryption key and a salt and stores the encrypted password to file
    Every 24 hours the salt expires and is regenerated
    """

    def __init__(self, store_encrypted_password=True):
        self.secret_file = None
        self.secret = None
        self.password_file = None
        self.salt_files = None
        self.latest_salt_file = None
        self.timeout = 60 * 60 * 24
        self.store_encrypted_password = store_encrypted_password
        if self.store_encrypted_password is False:
            self.reset()

    def setup(self):
        if self.secret is None:
            self.secret_file = Path(environ["HOME"]) / ".kp" / ".secret"
            if self.store_encrypted_password:
                if not self.secret_file.exists():
                    # generate a secret
                    key = Fernet.generate_key()
                    self.secret = key
                    self.secret_file.write_bytes(key)
                else:
                    self.secret = self.secret_file.read_bytes()
            self.password_file = Path(environ["HOME"]) / ".kp" / ".pass"
            self.salt_files = list((Path(environ["HOME"]) / ".kp").glob(".salt_*"))
            self.latest_salt_file = max(self.salt_files) if self.salt_files else None

    def get_password(self):
        self.setup()
        if self.latest_salt_file is not None and self.password_file.exists():
            timestamp = float(self.latest_salt_file.name.split("_")[-1])
            # check timestamp and delete/refresh salt every 24 hrs
            if datetime.now().timestamp() - timestamp > self.timeout:
                self.reset()
                return
            fernet = Fernet(self.secret)
            salt = self.latest_salt_file.read_text()
            password_with_salt = self.password_file.read_bytes()
            password = (
                fernet.decrypt(password_with_salt).decode("utf-8").replace(salt, "")
            )
            return password

    def reset(self):
        self.setup()
        for salt_file in self.salt_files:
            salt_file.unlink()
        for filepath in [self.secret_file, self.password_file]:
            if filepath.exists():
                filepath.unlink()
        return

    def save_password(self, config):
        self.setup()
        salt_file = (
            Path(environ["HOME"]) / ".kp" / f".salt_{datetime.now().timestamp()}"
        )
        # Generate random salt, hash and save password and store on config obj
        salt = f"".join(random.choice(string.ascii_letters) for i in range(24))
        password_with_salt = f"{salt}{config.password}"
        salt_file.write_text(salt)
        fernet = Fernet(self.secret)
        self.password_file.write_bytes(fernet.encrypt(password_with_salt.encode()))
