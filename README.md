# kpcli

A simple command line tool to interact with KeePassX databases.

[KeePassX](https://www.keepassx.org/) is a cross platform password management application.
It is available as a GUI application for MacOSX, Linux and Windows and as an Android app (KeePassDroid), 
making it useful to manage passwords across multiple devices.

### Features
- View details: list groups and entries, get details for a single entry
- Add new entries and change passwords from the commandline
- Resolve conflicts: users may choose to keep their KeePassX database in a central location
such as Dropbox or other synchronisation software.  This results in "conflicting copies" being generated if 
a opens and updates the database from more than one device.  **kpcli** avoids these conflicts, and also provides 
a utility to compare conflicting copies and identify where the conflicts lie.

## Installation

Using pip:

```pip install kpcli```

From source:

```
git clone https://github.com/rebkwok/kpcli.git
cd kpcli
poetry install
```

## Configuration

**kpcli** will look for database configuration first in a config.ini file, and if 
one is not found, in environment variables.

**NOTE:** 
AT YOUR OWN RISK! `KEEPASSDB_PASSWORD` can be set in the config.ini file or as an environment variable if you really want to.
Not advised unless you implement some method of encrypting and retrieving it before passing to **kpcli**.  If no `KEEPASSDB_PASSWORD`
is found, **kpcli** will prompt for it.

### Config file 

Create a config file at $(HOME)/.kp/config.ini, with at least a default profile, and your
database location and credentials:
```
[default]
KEEPASSDB=/Users/me/mypassworddb.kdbx
```

If your database uses a key file, provide that location too:
```
[default]
KEEPASSDB=/path/to/mypassworddb.kdbx
KEYPASSDB_KEYFILE=/path/to/mykeyfile.key
```

More than one profile can be set for multiple databases, and switched with the `-p` flag
```
[default]
KEEPASSDB=/path/to/db.kdbx
KEYPASSDB_KEYFILE=/path/to/mykeyfile.key

[work]
KEEPASSDB=/path/to/workdb.kdbx
```

### Environment Variables
If no config.ini file exists, **kpcli** will attempt to find config in the environment variables 
`KEEPASSDB`, `KEYPASSDB_KEYFILE` and `KEEPASSDB_PASSWORD` (falling back to a prompt for the password).


### Usage Examples ###

List groups and entries
```console
$kpcli ls

Database: /path/to/db.kdbx
================================================================================
Groups
================================================================================
Root
Internet
Communications
...

$kpcli ls --group comm --entries
Database: /path/to/db.kdbx
================================================================================
Communications
================================================================================
my email
work email
...
```

List groups in the database from the "work" profile:
```console
$kpcli --profile work ls
Database: /path/to/workdb.kdbx
================================================================================
Groups
================================================================================
Root
Work
...
```

Get an entry  
By group and entry title, separated with /.  Note partial matches are allowed.  
If multiple matching entries are found, all will be listed.
```console
$kpcli get comm/email
Database: /path/to/db.kdbx
================================================================================
Communications/my email
================================================================================
name: Communications/my email
username: my@email.com
password: **********
URL:
Notes: This is my main email address
```

Copy an attribute (default password) from an entry to the clipboard  
If multiple entries match, kpcli prompts for a selection.
```console
$kpcli cp comm/email
Entry: Communications/my email
password copied to clipboard

$kpcli cp comm/email username
Entry: Communications/my email
username copied to clipboard
```

Add an entry
```console
$kpcli add
```
**kpcli** will prompt for required fields.


Change a password
```console
$kpcli change-password comm/email
```
**kpcli** will prompt for new password.


For more detailed usage, use `--help` with any kpcli command listed below.

**Usage**:

```console
$ kpcli [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `-p, --profile TEXT`: Specify config profile to use  [default: default]
* `--loglevel TEXT`: [default: INFO]
* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `ls`: List groups and entries
* `get`: Fetch details for a single entry
* `cp`: Copy entry attribute to clipboard
* `add`: Add a new entry
* `change-password`: Change entry password
* `compare`: Compare potentially conflicting copies of a KeePassX Database and report conflicts




