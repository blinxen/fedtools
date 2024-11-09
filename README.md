fedtools
========

CLI tool that helps with various Fedora packaging processes.

Commands
--------

* `build-srpm`: Download all sources, build SRPM locally and build the package using `mock`
* `check-versions`: Compare package version with the latest upstream release
* `review`: Download spec and SRPM from URLs in review bug
* `fp-upload`: Upload spec file and SRPM in the current working directory to fedorapeople
* `copr-review`: Build SRPM in copr and run fedora-review after build
* `post-rust-review`: Run some rust specific tasks after a package review
* `copr-chain-build`: Create a chain-build in copr

Configuration
-------------

The configuration file for `fedtools` must be places under `$HOME/.config/fedtools.toml`.
See [fedtools.toml](./example/fedtools.toml) for an example.

Development
-----------

```
poetry install
poetry run fedtools
```

Installation
------------

Fedora:

```
dnf copr enable blinxen/tools
dnf install fedtools
```

License
-------

The source code is primarily distributed under the terms of the MIT License.
See LICENSE for details.
