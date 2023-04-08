import os
import subprocess
from argparse import Namespace
from pathlib import Path


def get_files_to_upload() -> list[str]:
    files = []
    for file in os.listdir("./"):
        if file.endswith(".spec") or file.endswith(".src.rpm"):
            files.append(file)

    return files


def get_username(username: str) -> str:
    try:
        with open(os.path.join(Path.home(), ".fedora.upn")) as f:
            username = f.read()
    except Exception:
        # We don't really care why we can't read it
        pass

    if username is None:
        print(
            "Username was not specified with --username or HOME/fedora.upn does not exist"
        )
        exit(1)

    return username


def upload(args: Namespace):
    files = get_files_to_upload()
    username = get_username(args.username)

    if files:
        print(f"Uploading: {' and '.join(files)}")
        remote = f"{username}@fedorapeople.org"
        package_path = os.path.join(
            f"/home/fedora/{username}/public_html/{os.path.basename(os.getcwd())}"
        )

        # Create directory
        subprocess.run(
            ["ssh", remote, "mkdir", "-p", package_path]
        )
        subprocess.run([
            "rsync",
            " ".join(files),
            f"{remote}:{package_path}",
        ])
    else:
        print("No files to upload!")
