import argparse
from argparse import ArgumentParser
from fedtools import check_upstream_versions
from fedtools import build_srpm
from fedtools import review


def register_check_versions_command(parser: ArgumentParser):
    parser.set_defaults(func=check_upstream_versions.check_versions)


def register_build_command(parser: ArgumentParser):
    parser.add_argument("specfile")
    parser.add_argument("--arch", required=False, default=None)
    parser.add_argument("--mock", required=False, action="store_true")
    parser.add_argument("--mock-root", required=False, default="fedora-rawhide-x86_64")
    parser.set_defaults(func=build_srpm.build)


def register_review_command(parser: ArgumentParser):
    parser.add_argument("bug")
    parser.add_argument("-y", required=False, action="store_true")
    parser.set_defaults(func=review.make)


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
    # Download files that make package review easier
    register_review_command(
        subparsers.add_parser(
            "review",
            help="Download spec and SRPM from URLs in review bug.\n"
            "Optionally also download review.txt from fedora-review-service",
        )
    )

    args = parser.parse_args()
    args.func(args)


if "__main__" == __name__:
    main()
