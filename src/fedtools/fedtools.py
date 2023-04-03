import argparse
from argparse import Namespace
from fedtools import check_upstream_versions
from fedtools import build_srpm


def check_versions(args: Namespace):
    check_upstream_versions.check_versions()


def build(args: Namespace):
    build_srpm.build(args.filename, args.arch, args.mock, args.mock_root)


def main():
    parser = argparse.ArgumentParser(
        prog="fedtools",
        description="Collection of python scripts that help with fedora packaging / maintanence tasks",
    )
    subparsers = parser.add_subparsers(dest='command', required=True)
    # Build SRPM
    build_parser = subparsers.add_parser(
        "build", help="Build SRPM and move it to the current directory"
    )
    build_parser.add_argument("filename")
    build_parser.add_argument("--arch", required=False, default=None)
    build_parser.add_argument("--mock", action="store_true")
    build_parser.add_argument("--mock-root", required=False, default="fedora-rawhide-x86_64")
    build_parser.set_defaults(func=build)
    # Check rpm versions
    check_versions_parser = subparsers.add_parser(
        "check-versions", help="Pretty print a diff of packaged version and upstream version"
    )
    check_versions_parser.set_defaults(func=check_versions)

    args = parser.parse_args()
    args.func(args)


if "__main__" == __name__:
    main()
