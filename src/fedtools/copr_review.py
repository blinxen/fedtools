from argparse import Namespace
from fedtools.utils import exec_cmd


def build(args: Namespace):

    if not args.srpm.endswith(".src.rpm"):
        print("ERROR: Only SRPM files are accepted")
        exit(1)

    copr_project_name = f"fedora-review-{args.srpm[:-8]}"

    copr_repo = exec_cmd(
        "copr-cli",
        [
            "create",
            "--chroot",
            "fedora-rawhide-x86_64",
            "--chroot",
            "fedora-39-x86_64",
            "--chroot",
            "fedora-38-x86_64",
            "--chroot",
            "fedora-37-x86_64",
            "--fedora-review",
            copr_project_name,
        ],
        tail_command=True,
    )

    if copr_repo.returncode != 0:
        print("ERROR: Could not create copr project")
    try:
        exec_cmd("copr-cli", ["build", copr_project_name, args.srpm], tail_command=True)
    except KeyboardInterrupt:
        print("Ctrl-c was pressed")
