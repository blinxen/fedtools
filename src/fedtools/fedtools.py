import argparse
from argparse import ArgumentParser
from fedtools import check_upstream_versions
from fedtools import build_srpm


def register_check_versions_command(parser: ArgumentParser):
    parser.set_defaults(func=check_upstream_versions.check_versions)


def register_build_command(parser: ArgumentParser):
    parser.add_argument("filename")
    parser.add_argument("--arch", required=False, default=None)
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--mock-root", required=False, default="fedora-rawhide-x86_64")
    parser.set_defaults(func=build_srpm.build)


def main():
    parser = argparse.ArgumentParser(
        prog="fedtools",
        description="Collection of python scripts that help with fedora packaging / maintanence tasks",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    # Build SRPM
    register_build_command(
        subparsers.add_parser(
            "build", help="Build SRPM and move it to the current directory"
        )
    )
    # Check rpm versions
    register_check_versions_command(
        subparsers.add_parser(
            "check-versions",
            help="Pretty print a diff of packaged version and upstream version",
        )
    )

    args = parser.parse_args()
    args.func(args)


if "__main__" == __name__:
    main()
