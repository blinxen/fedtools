from argparse import Namespace
from fedtools.utils import exec_cmd


def build(args: Namespace):

    if not args.srpm.endswith(".src.rpm"):
        print("ERROR: Only SRPM files are accepted")
        exit(1)

    # We ask for the name because this is the simplest solution for now and I am too
    # lazy to get it automatically
    name = input("What is the name of the package?\n")
    if len(name) < 5:
        print("Name must consist of at leat 5 characters")
        exit(1)

    copr_project_name = f"fedora-review-{name}"

    copr_repo = exec_cmd(
        "copr-cli",
        [
            "create",
            "--chroot",
            args.chroot,
            "--fedora-review",
            copr_project_name,
        ],
        tail_command=True,
    )

    if copr_repo.returncode != 0:
        print("ERROR: Could not create copr project")

    exec_cmd("copr-cli", ["build", copr_project_name, args.srpm], tail_command=True)
