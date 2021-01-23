#!/usr/bin/env python3

def find_entries(db, search):
    search = search.split("/")
    if len(search) > 1:
        group, title = search
        group = db.find_groups(name=group, regex=True, flags="i", first=True)
        return db.find_entries(title=title, group=group, regex=True, flags="i")
    else:
        title = search[0]
        return db.find_entries(title=title, regex=True, flags="i")


def add_new_entry(db):
    group = None
    print("New entry:")
    while group is None:
        group_name = input("Group name (leave empty for Root group: ")
        group = db.find_groups(name=group_name, regex=True, flags="i", first=True)
        if group is None:
            print("No matching group found, please enter one of the following groups: {group_names}")

    title = None
    while not title:
        title = input("Title: ")
        if not title:
            print("Title is required")
        else:
            existing_entries = db.find_entries(title=title, group=group, recursive=False, regex=True, flags="i")
            if existing_entries:
                print("An entry already exists for that group/title, please enter a different title.")
                title = None

    username = input("Username: ")
    password = input("Password: ")
    url = input("Url: ")
    notes = input("Notes: ")
    db.add_entry(group, title, username, password, url=url, notes=notes)
    db.save()
    print("================================")
    print(f"New entry added:  {group.name}/{title}\nUsername {username}\nPassword {'*' * len(password)}\nURL: {url}\nNotes: {notes}")
