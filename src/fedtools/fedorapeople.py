import os
from argparse import Namespace
from pathlib import Path
from fedtools.utils import exec_cmd, LOGGER


FEDORA_PEOPLE_URL = "https://blinxen.fedorapeople.org"


def get_files_to_upload(path: str) -> list[str]:
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
        LOGGER.error(
            "Username was not specified with --username and $HOME/.fedora.upn does not exist!\n"
            "Either define --username or create the $HOME/.fedora.upn file."
        )
        exit(1)

    return username


def upload(args: Namespace):
    files = get_files_to_upload(args.path)
    username = get_username(args.username)

    if files:
        LOGGER.info(f"Uploading: {' and '.join(files)}")
        remote = f"{username}@fedorapeople.org"
        # Name of the package directory
        package_directory = os.path.basename(os.path.abspath(args.path))
        # Absolute path to the package directory
        package_path = os.path.join(
            f"/home/fedora/{username}/public_html/{package_directory}"
        )

        # Create directory

        exec_cmd(
            "ssh",
            [remote, "mkdir", "-p", package_path],
            error_msg="Could not create target directory on the fedorapeople server!",
        )
        exec_cmd(
            "rsync",
            [*files, f"{remote}:{package_path}"],
            error_msg="Could not upload the files to the fedorapeople server!",
        )

        LOGGER.info("Links to the uploaded files:")
        for file in files:
            prefix = ""
            if file.endswith(".spec"):
                prefix = "Spec URL: "
            elif file.endswith(".src.rpm"):
                prefix = "SRPM URL: "

            LOGGER.info(
                f"{prefix}{FEDORA_PEOPLE_URL}/{package_directory}/{os.path.basename(file)}"
            )
    else:
        LOGGER.error("No files to upload!")
