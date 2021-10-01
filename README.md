[![PyPI version](https://badge.fury.io/py/requre.svg)](https://badge.fury.io/py/requre)

# REQUest REcording

Requre \[rekure\]

Is a library for storing output of various function and methods to
persistent storage and be able to replay the stored output to functions
back

[Documentation](https://requre.readthedocs.io/en/latest/)

## Plan and current status

- Used for testing [packit-service](https://github.com/packit-service) organization projects
  - ogr
  - packit

## Installation

On Fedora:

```
$ dnf install python3-requre
```

Or from PyPI:

```
$ pip3 install --user requre
```

You can also install `requre` from `main` branch, if you are brave enough:

You can use our [`packit/packit-dev` Copr repository](https://copr.fedorainfracloud.org/coprs/packit/packit-dev/):

```
$ dnf copr enable packit/packit-dev
$ dnf install python3-requre
```

Or

```
$ pip3 install --user git+https://github.com/packit/requre.git
```
