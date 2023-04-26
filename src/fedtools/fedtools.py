# PYTHON_ARGCOMPLETE_OK

import argcomplete
import argparse
from argparse import ArgumentParser
from fedtools import check_upstream_versions
from fedtools import build_srpm
from fedtools import review
from fedtools import fedorapeople


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


def register_fedorapeople_upload(parser: ArgumentParser):
    parser.add_argument(
        "--path",
        required=False,
        default="./",
        help="Path to directory, where the SPEC and SRPM files"
        "should reside. Defaults to the current path",
    )
    parser.add_argument("--username", required=False, default=None)
    parser.set_defaults(func=fedorapeople.upload)


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
    # Copy files to fedorapeople to use in a package review
    register_fedorapeople_upload(
        subparsers.add_parser(
            "fp-upload",
            help="Upload spec file and SRPM in the current working directory to fedorapeople."
            "This command will create a directory under /home/fedora/USERNAME/public_html "
            "which will be named after the directory in which this command was executed in.\n"
            "This will only work if you have set up the access to fedorapeople beforehand.",
        )
    )

    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    args.func(args)


if "__main__" == __name__:
    main()
