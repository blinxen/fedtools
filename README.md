# fedtools

CLI tool that helps with various Fedora packaging processes.

```
usage: fedtools [-h] {build-srpm,check-versions,review,fp-upload,copr-review,post-rust-review} ...

Collection of python scripts that help with fedora packaging / maintanence tasks

positional arguments:
  {build-srpm,check-versions,review,fp-upload,copr-review,post-rust-review}
    build-srpm          Download all sources and build SRPM.
                        Optionally, also execute mock (+rpmlint) on the built SRPM.
    check-versions      Pretty print a diff of packaged version vs upstream version.
    review              Download spec and SRPM from URLs in review bug.
                        Optionally, also download review.txt from fedora-review-service.
    fp-upload           Upload spec file and SRPM in the current working directory to fedorapeople.
                        This command will create a directory under `/home/fedora/USERNAME/public_html`
                        which will be named after the directory in which this command was executed in.
                        This will only work if you have set up the access to fedorapeople beforehand.
    copr-review         Build SRPM in copr and run fedora-review after build.
                        This command assumes the following:
                            1. copr-cli is installed and configured properly
                            2. You only want to build in rawhide,f39,f38
    post-rust-review    This command does the following tasks:
                            1. Add package to release-monitoring.org
                            2. Give 'rust-sig' commit access to the package repository

options:
  -h, --help            show this help message and exit
```

## Configuration

The configuration file for `fedtools` must be places under `$HOME/.config/fedtools.toml`.
See [fedtools.toml](./fedtools.toml) for an example.

## Development

```
poetry lock
poetry install
poetry run fedtools
```

## Install

Fedora:

```
dnf copr enable blinxen/python-fedtools
dnf install fedtools
```
