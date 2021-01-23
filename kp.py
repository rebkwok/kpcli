#!/usr/bin/env python3
# standard
import logging
from os import environ
from pathlib import Path

# third parties
import typer

from comparator import KpDatabaseComparator
from datastructures import KpConfig, KpContext
from connector import KpDatabaseConnector

logger = logging.getLogger(__name__)
app = typer.Typer()


def get_config():
    missing_config = [var for var in ["KEEPASSDB", "KEEPASSDB_PASSWORD"] if environ.get(var) is None]
    if missing_config:
        logger.error("Missing environment variable(s): %s", ", ".join())
        return None
    db_config = KpConfig(filename=Path(environ["KEEPASSDB"]), password=environ["KEEPASSDB_PASSWORD"],
                         keyfile=environ.get("KEEPASSDB_KEYFILE"))
    if not db_config.filename.exists():
        logger.error("Database file %s does not exist", db_config.filename)
        return None
    return db_config


@app.command()
def compare(ctx: typer.Context):
    typer.echo("Looking for conflicting files...")
    db_config = get_config()
    if db_config is None:
        return
    ctx.obj.compare_for_conflicts()


def ctx_connector(ctx: typer.Context):
    return ctx.obj.connector


def echo_banner(message):
    banner = "=" * 50
    typer.echo(f"{banner}\n{message}\n{banner}")


@app.command()
def list_groups(
    ctx: typer.Context,
    entries: bool = typer.Option(False, help="Include entries for groups.")
):
    group_names = ctx_connector(ctx).list_group_names()
    if entries:
        for group_name in group_names:
            list_entries(ctx, group_name)
    else:
        group_names = "\n".join(group_names)
        echo_banner("Groups")
        typer.echo(group_names)

@app.command()
def list_entries(ctx: typer.Context, group_name: str):
    entry_names = "\n".join(ctx_connector(ctx).list_group_entries(group_name))
    echo_banner(f"{group_name}")
    typer.echo(entry_names)


def validate_group(ctx: typer.Context, group_name):
    group = ctx_connector(ctx).find_group(group_name)
    if group is None:
        typer.echo(f"No group matching '{group_name}' found")
        raise typer.Abort()
    typer.echo(f"Group found: {group.name}")
    ctx.obj.group = group
    return group


def validate_title(ctx: typer.Context, title):
    group = ctx.obj.group
    existing_entries = ctx_connector(ctx).find_entries_by_title(title, group)
    if existing_entries:
        typer.echo(f"An entry already exists for '{title}' in group {group.name}")
        raise typer.Abort()
    return title


@app.command()
def add(
        ctx: typer.Context,
        group: str = typer.Option(default="root", prompt="Group name", callback=validate_group),
        title: str = typer.Option(..., prompt=True, callback=validate_title),
        username: str = typer.Option(..., prompt=True),
        password: str = typer.Option(..., prompt=True, hide_input=True),
        url: str = typer.Option(default="", prompt=True),
        notes: str = typer.Option(default="", prompt=True),
    ):
    ctx_connector(ctx).add_new_entry(group, title, username, password, url, notes)
    echo_banner("New entry added")
    typer.echo(
        f"{group.name}/{title}\nUsername {username}\nPassword {'*' * len(password)}\nURL: {url}\nNotes: {notes}"
    )


@app.command()
def get(
        ctx: typer.Context,
        name: str = typer.Argument(..., help="group/title of item to fetch"),
        show_password: bool = typer.Option(False, help="Show password"),
    ):
        entries = ctx_connector(ctx).find_entries(name)
        if not entries:
            typer.echo("No matching entry found")
            typer.Exit()
        for entry in entries:
            ctx_connector(ctx).get_details(entry, show_password)


def validate_selection(option_count):
    selection = typer.prompt(f"Select entry number")
    try:
        selection = int(selection)
    except ValueError:
        return selection, False
    return selection, 1 <= selection <= option_count


def get_single_entry(ctx: typer.Context, name):
    entries = ctx_connector(ctx).find_entries(name)
    if not entries:
        typer.echo("No matching entry found")
        typer.Exit()
    if len(entries) > 1:
        typer.echo(f"Multiple matching entries found: ")
        for i, entry in enumerate(entries, start=1):
            typer.echo(f"{i}: {entry.group.name}/{entry.title}")

        selection, is_valid = validate_selection(len(entries))
        while is_valid is False:
            typer.echo(f"Invalid selection {selection}; try again")
            selection, is_valid = validate_selection(len(entries))
        return entries[selection - 1]
    else:
        return entries[0]


@app.command()
def copy(
        ctx: typer.Context,
        name: str = typer.Argument(..., help="group/title of item to fetch"),
        item: str = typer.Argument("password", help="Attribute to copy"),
):
    entry = get_single_entry(ctx, name)
    typer.echo(f"Entry: {entry.group.name}/{entry.title}")
    ctx_connector(ctx).copy_to_clipboard(entry, item)


@app.command()
def change_password(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="group/title of item to fetch"),
    password: str = typer.Option(..., prompt="New password", hide_input=True),
):
    entry = get_single_entry(ctx, name)
    ctx_connector(ctx).change_password(entry, password)


@app.callback()
def main(ctx: typer.Context):
    """Instantiates the relevant database utility object on the Context"""
    if ctx.invoked_subcommand == "compare":
        ctx.obj = KpDatabaseComparator(get_config())
    else:
        ctx.obj = KpContext(connector=KpDatabaseConnector(get_config()))


if __name__ == "__main__":
    logging.basicConfig(level=environ.get("LOGLEVEL", "INFO"))
    app()
