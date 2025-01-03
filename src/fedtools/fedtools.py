# PYTHON_ARGCOMPLETE_OK

import argcomplete
import argparse
from argparse import ArgumentParser
from fedtools import check_upstream_versions
from fedtools import build_srpm
from fedtools import review
from fedtools import fedorapeople
from fedtools import copr_review
from fedtools import post_rust_review
from fedtools import copr_chain_build


def register_check_versions_command(parser: ArgumentParser):
    parser.add_argument(
        "--path",
        required=False,
        default="./",
        help="Path to parent directory of all package directories",
    )
    parser.set_defaults(func=check_upstream_versions.check_versions)


def register_build_srpm_command(parser: ArgumentParser):
    parser.add_argument("specfile")
    parser.add_argument("--arch", required=False, default=None)
    parser.add_argument("--mock", required=False, action="store_true")
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


def register_copr_review_command(parser: ArgumentParser):
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--srpm", help="Path to SRPM")
    group.add_argument(
        "--cleanup",
        help=f"Delete all copr projects that have {copr_review.REVIEW_PREFIX} as a prefix",
        action="store_true",
    )
    parser.set_defaults(func=copr_review.build)


def register_rust_review_command(parser: ArgumentParser):
    parser.add_argument("package_name", help="Name of the package")
    parser.set_defaults(func=post_rust_review.make)


def register_copr_chain_build_command(parser: ArgumentParser):
    parser.add_argument(
        "config_toml",
        help="Path to the configuration file.\n",
    )
    parser.add_argument(
        "--generate-fedpkg-command",
        required=False,
        action="store_true",
        help="Generate a fedpkg chain-build command instead of building in copr",
    )
    parser.set_defaults(func=copr_chain_build.build)


def main():
    parser = argparse.ArgumentParser(
        prog="fedtools",
        description="Collection of python scripts that help with fedora packaging / maintanence tasks",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    # Build SRPM
    register_build_srpm_command(
        subparsers.add_parser(
            "build-srpm",
            help="Download all sources and build SRPM.\n"
            "Optionally, also execute mock (+rpmlint) on the built SRPM.",
        )
    )
    # Check rpm versions
    register_check_versions_command(
        subparsers.add_parser(
            "check-versions",
            help="Compare package version with the latest upstream release.",
        )
    )
    # Download files that make package review easier
    register_review_command(
        subparsers.add_parser(
            "review",
            help="Download spec and SRPM from URLs in review bug.\n"
            "Optionally, also download review.txt from fedora-review-service.",
        )
    )
    # Copy files to fedorapeople to use in a package review
    register_fedorapeople_upload(
        subparsers.add_parser(
            "fp-upload",
            help="Upload spec file and SRPM in the current working directory to fedorapeople.\n"
            "This command will create a directory under `/home/fedora/USERNAME/public_html`\n"
            "which will be named after the directory in which this command was executed in.\n"
            "This will only work if you have set up the access to fedorapeople beforehand.",
        )
    )
    # Run fedora-review in copr
    register_copr_review_command(
        subparsers.add_parser(
            "copr-review",
            help="Build SRPM in copr and run fedora-review after build.\n"
            "This command assumes the following:\n"
            "\t1. copr-cli is installed and configured properly\n"
            "\t2. You only want to build in rawhide,f39,f38".expandtabs(4),
        )
    )
    # Rust sig tasks after a package review
    register_rust_review_command(
        subparsers.add_parser(
            "post-rust-review",
            help="This command does the following tasks:\n"
            "\t1. Add package to release-monitoring.org\n"
            "\t2. Give 'rust-sig' commit access to the package repository\n".expandtabs(
                4
            ),
        )
    )
    # Start a chain build in copr
    register_copr_chain_build_command(
        subparsers.add_parser(
            "copr-chain-build", help="Create a chain-build using copr"
        )
    )

    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    args.func(args)


if "__main__" == __name__:
    main()
