0.4.1
-----
- Rename `name` argument to `cp` to `entry`

0.4.0
-----
- Option to copy both username and password

0.3.0
-----
- Drop support for Python 3.6
- Update dependencies
- Fix bug for entries with no password (PR#6 from @delameter)
- Initiate database setup after calling subcommand; this means that
`kpcli <subcommand> --help` doesn't prompt for the db password

0.2.5
-----
Bump

0.2.4
-----
Fix bug if salt files deleted

0.2.3
-----
Bugfix

0.2.2
-----
- Option to store encrypted password

0.2.1
-----
- Clear clipboard after a timeout on password copying

0.2.0
-----
New commands:

- Add and delete group
- Edit entry fields
- Delete entry

0.1.0
-----
- List groups, entries
- Get entry details
- Copy entry attributes to clipboard
- Add new entry
- Change password
- Compare conflicting databases
