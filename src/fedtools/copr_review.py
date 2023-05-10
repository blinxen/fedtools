from argparse import Namespace
import subprocess
import sys


def build(args: Namespace):
    # We ask for the name because this is the simplest solution for now and I am too
    # lazy to get it automatically
    name = input("What is the name of the package?\n")
    if len(name) < 5:
        print("Name must consist of at leat 5 characters")
        exit(1)

    copr_project_name = f"fedora-review-{name}"

    copr_repo = subprocess.run(
        [
            "copr-cli",
            "create",
            "--chroot",
            "fedora-rawhide-x86_64",
            "--fedora-review",
            copr_project_name,
        ],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    if copr_repo.returncode != 0:
        print("ERROR: Could not create copr project")
        exit(1)

    subprocess.run(
        ["copr-cli", "build", copr_project_name, args.srpm],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
