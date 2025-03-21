# 0.9.1

- Adjusted `requre-purge` to not replace GitHub tokens with dummy token that
  still looks like a legit one and also case-sensitiveness on the cookies from
  Pagure.

# 0.9.0

- Supports recording of the requests done by `httpx` via `record_httpx()` and `recording_httpx()` decorators. (#297)

# 0.8.6

- Trigger a new release to fix the PyPI upload action.

# 0.8.5

- Trigger a new release to confirm the correct SPDX licence.

# 0.8.4

- Provide `__version__` of the package so it can be easily checked when installed on the system.

# 0.8.3

- Fix an issue of clashing with the _coverage_.
- Packaging has been modernized.

# 0.8.2

- No user-facing changes.

# 0.8.1

- Fix the problem with kwarg decorators that causes the function body not to be executed.

# 0.8.0

- New decorators for handling temporary files (MkTemp) and directories (MkDTemp) in a more transparent way.
- The old implementation based on static paths and counter has been deprecated.

# 0.7.1

- Fix a performance issue when detecting cassettes following the old naming format.

# New release 0.7.0

- New version of requre 0.7.0

# New release 0.6.1

- python 'tuple' support as base type

# new version 0.6.0

- release new version 0.6.0

# simplify user experience

Features

- default decorator if not given
- guess output decorator class
- class shortcut decorators

# new version 0.4.0

- repair specfile to be same as possible as in ogr and packit.yaml fix
