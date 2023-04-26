import os
import subprocess
from argparse import Namespace
from pathlib import Path


def get_files_to_upload(path) -> list[str]:
    files = []
    if os.path.exists(path):
        for file in os.listdir(path):
            if file.endswith(".spec") or file.endswith(".src.rpm"):
                files.append(os.path.join(path, file))

    return files


def get_username(username: str) -> str:
    # If username was not specified then look for it in fedora.upn
    if username is None:
        try:
            with open(os.path.join(Path.home(), ".fedora.upn")) as f:
                username = f.read()
        except Exception:
            # We don't really care why we can't read it
            pass

    if username is None:
        print(
            "Username was not specified with --username and HOME/fedora.upn does not exist"
        )
        exit(1)

    return username


def upload(args: Namespace):
    files = get_files_to_upload(args.path)
    username = get_username(args.username)

    if files:
        print(f"Uploading: {' and '.join(files)}")
        remote = f"{username}@fedorapeople.org"
        package_path = os.path.join(
            f"/home/fedora/{username}/public_html/{os.path.basename(os.path.abspath(args.path))}"
        )

        # Create directory
        subprocess.run(["ssh", remote, "mkdir", "-p", package_path])
        subprocess.run(
            [
                "rsync",
                *files,
                f"{remote}:{package_path}",
            ]
        )
    else:
        print("No files to upload!")
