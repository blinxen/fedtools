from argparse import Namespace

# https://python-copr.readthedocs.io/en/latest/ClientV3.html
from copr.v3 import Client
from copr.v3.exceptions import CoprRequestException
import os

from fedtools.utils import create_copr_repo, copr_build, LOGGER


CHROOTS = [
    "fedora-rawhide-x86_64",
    "fedora-rawhide-aarch64",
    "fedora-rawhide-s390x",
    "fedora-rawhide-ppc64le",
]
REVIEW_PREFIX = "fedora-review"


def create_copr_repo(client: Client, project_name: str):
    try:
        client.project_proxy.add(
            client.base_proxy.auth_username(), project_name, CHROOTS, fedora_review=True
        )
    except CoprRequestException as e:
        print(Colors.RED + str(e) + Colors.RESET)


def copr_build(client: Client, project_name: str, srpm_path: str) -> int:
    build = client.build_proxy.create_from_file(
        client.base_proxy.auth_username(), project_name, srpm_path
    )
    return build.id


def cleanup_review_copr_repos(client):
    projects = client.project_proxy.search(
        f"{client.base_proxy.auth_username()}/{REVIEW_PREFIX}"
    )
    for project in projects:
        client.project_proxy.delete(client.base_proxy.auth_username(), project["name"])


def build(args: Namespace):
    if args.srpm is None and args.cleanup is False:
        LOGGER.error("No command specified, use --help to see all options.")
        exit(1)

    client = Client.create_from_config_file()
    if args.cleanup is True:
        cleanup_review_copr_repos(client)
        exit(0)

    if not args.srpm.endswith(".src.rpm"):
        LOGGER.error("Only SRPM files are accepted")
        exit(1)

    copr_project_name = f"{REVIEW_PREFIX}-{os.path.basename(args.srpm)[:-8]}"

    create_copr_repo(client, copr_project_name)
    build_id = copr_build(client, copr_project_name, args.srpm)
    LOGGER.info(
        f"https://copr.fedorainfracloud.org/coprs/{client.base_proxy.auth_username()}/{copr_project_name}/build/{build_id}/"
    )
