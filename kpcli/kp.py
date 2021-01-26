#!/usr/bin/env python3
# standards
import logging
from typing import Optional

# third parties
from pykeepass.exceptions import CredentialsError
import typer

from kpcli.comparator import KpDatabaseComparator
from kpcli.datastructures import CopyOption, KpContext
from kpcli.connector import KpDatabaseConnector
from kpcli.utils import echo_banner, get_config

logger = logging.getLogger(__name__)
app = typer.Typer()


############
# VALIDATORS
############


def validate_group(ctx: typer.Context, group_name):
    """Find the first group matching group_name"""
    group = ctx_connector(ctx).find_group(group_name)
    if group is None:
        typer.echo(f"No group matching '{group_name}' found")
        raise typer.Exit()
    typer.echo(f"Group found: {group.name}")
    ctx.obj.group = group
    return group


def validate_title(ctx: typer.Context, title):
    """
    Validate title when adding a new entry and abort if an entry already exists with the requested title
    """
    # group should already be set, either at the command line or from a prompt
    group = ctx.obj.group
    if group is None:
        # group may be None if a user specified --title at the command line
        typer.echo(f"--group is required")
        raise typer.Exit()

    existing_entries = ctx_connector(ctx).find_entries(title, group)
    if existing_entries:
        typer.echo(f"An entry already exists for '{title}' in group {group.name}")
        raise typer.Abort()
    return title


def validate_selection_number(option_count):
    """
    Validate a selection prompt from the user and ensure it is one of the valid options
    """
    selection = typer.prompt(f"Select entry number")
    try:
        selection = int(selection)
    except ValueError:
        return selection, False
    return selection, 1 <= selection <= option_count


@app.command()
def compare(ctx: typer.Context, show_details: bool = False):
    """
    Compare potentially conflicting copies of a KeePassX Database and report conflicts

    If a KeePassX database is opened and modified from multiple locations, KeePassX will create a duplicate
    with the suffix `_conflicting_copy`
    """
    typer.echo("Looking for conflicting files...")
    conflicting_tables = ctx.obj.generate_tables_of_conflicts(show_details=show_details)
    if not conflicting_tables:
        typer.echo("No conflicting tables found")
    for conflicting_table_name, conflicting_table in conflicting_tables.items():
        echo_banner(f"Comparison db: {conflicting_table_name}", fg=typer.colors.RED)
        typer.echo(conflicting_table)


def ctx_connector(ctx: typer.Context):
    """Helper function to retrieve KpDatabaseConnector set on context"""
    return ctx.obj.connector


@app.command("ls")
def list_groups_and_entries(
    ctx: typer.Context,
    group_name: Optional[str] = typer.Option(
        None, "--group", "-g", help="Group name (partial allowed)"
    ),
    entries: bool = typer.Option(False, "--entries", "-e", help="Also list entries"),
):
    """
    List groups and entries
    """
    if group_name:
        group = ctx_connector(ctx).find_group(group_name)
        group_names = [group.name]
    else:
        group_names = ctx_connector(ctx).list_group_names()

    if entries:
        for group_name in group_names:
            entry_names = "\n".join(ctx_connector(ctx).list_group_entries(group_name))
            echo_banner(f"{group_name}", fg=typer.colors.GREEN)
            typer.echo(entry_names)
    else:
        group_names = "\n".join(group_names)
        echo_banner("Groups", fg=typer.colors.GREEN)
        typer.echo(group_names)


@app.command("add")
def add_entry(
    ctx: typer.Context,
    group: str = typer.Option(
        "root", prompt="Group name (partial matches allowed)", callback=validate_group
    ),
    title: str = typer.Option(..., prompt=True, callback=validate_title),
    username: str = typer.Option(..., prompt=True),
    password: str = typer.Option(..., prompt=True, hide_input=True),
    url: str = typer.Option("", prompt=True),
    notes: str = typer.Option("", prompt=True),
):
    """
    Add a new entry
    """
    ctx_connector(ctx).add_new_entry(group, title, username, password, url, notes)
    echo_banner("New entry added")
    typer.echo(
        f"{group.name}/{title}\nUsername {username}\nPassword {'*' * len(password)}\nURL: {url}\nNotes: {notes}"
    )


@app.command("get")
def get_entry(
    ctx: typer.Context,
    name: str = typer.Argument(
        ...,
        help="Name (or partial name) of item to fetch.  Specify group with / e.g. root/my_item",
    ),
    show_password: bool = typer.Option(
        False, "--show-password", "-s", help="Show password"
    ),
):
    """
    Fetch details for a single entry
    """
    entries = ctx_connector(ctx).find_entries(name)
    if not entries:
        typer.echo("No matching entry found")
        raise typer.Exit()
    for entry in entries:
        details = ctx_connector(ctx).get_details(entry, show_password)
        echo_banner(details["name"])
        typer.echo("\n".join([f"{field}: {value}" for field, value in details.items()]))


def get_or_prompt_single_entry(ctx: typer.Context, name):
    """
    Find matching entries from the entered name, prompt user for a selection if multiple
    matches found
    """
    entries = ctx_connector(ctx).find_entries(name)
    if not entries:
        typer.echo("No matching entry found")
        raise typer.Exit(1)
    elif len(entries) > 1:
        typer.echo(f"Multiple matching entries found: ")
        for i, entry in enumerate(entries, start=1):
            typer.echo(f"{i}: {entry.group.name}/{entry.title}")

        selection, is_valid = validate_selection_number(len(entries))
        while is_valid is False:
            typer.echo(f"Invalid selection {selection}; try again")
            selection, is_valid = validate_selection_number(len(entries))
        return entries[selection - 1]
    else:
        return entries[0]


@app.command("cp")
def copy_entry_attribute(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="group/title (or part thereof) of entry"),
    item: CopyOption = typer.Argument(CopyOption.password, help="Attribute to copy"),
):
    """
    Copy entry attribute to clipboard (username, password or url)
    """
    entry = get_or_prompt_single_entry(ctx, name)
    typer.echo(f"Entry: {entry.group.name}/{entry.title}")
    ctx_connector(ctx).copy_to_clipboard(entry, str(item))
    typer.secho(f"{str(item)} copied to clipboard", fg=typer.colors.GREEN)


@app.command()
def change_password(
    ctx: typer.Context,
    name: str = typer.Argument(
        ..., help="group/title (or part thereof) of entry to fetch"
    ),
    new_password: str = typer.Option(
        ..., "--password", prompt="New password", hide_input=True
    ),
):
    """
    Change entry password
    """
    entry = get_or_prompt_single_entry(ctx, name)
    typer.echo(f"Entry: {entry.group.name}/{entry.title}")
    ctx_connector(ctx).change_password(entry, new_password)
    typer.secho(
        f"{entry.group.name}/{entry.title}: password updated", fg=typer.colors.GREEN
    )


@app.callback()
def main(
    ctx: typer.Context,
    profile: Optional[str] = typer.Option(
        "default", "--profile", "-p", help="Specify config profile to use"
    ),
    loglevel: Optional[str] = typer.Option("INFO"),
):
    """
    Interact with a KeePassX database

    Set the required config variable KEEPASSDB and (if the database requires it) KEEPASSDB_KEYFILE,
    either as environment variables or in a configuration file located at $(HOME)/.kp/config.ini

    Set additional profiles in config.ini to allow switching between different databases
    """
    logging.basicConfig(level=loglevel.upper())

    # Instantiate the relevant database utility object on the Context
    config = get_config(profile=profile)
    if config.password is None:
        # If a password wasn't found in the config file or environment, prompt the use for it
        config.password = typer.prompt("Database password", hide_input=True)

    try:
        if ctx.invoked_subcommand == "compare":
            ctx.obj = KpDatabaseComparator(config)
        else:
            ctx.obj = KpContext(connector=KpDatabaseConnector(config))
    except CredentialsError:
        typer.secho(
            f"Invalid credentials for database {config.filename}", fg=typer.colors.RED
        )
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
