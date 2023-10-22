from argparse import Namespace
import requests
from fedtools.utils import Colors
from fedtools.config import Config


def monitor_package(crate_name: str, api_key: str):
    """Register package at release-monitoring.org

    Parameters:

        crate_name: Crate name that should be registered
        api_key: API key that should be used for authentication
    """
    # https://release-monitoring.org/static/docs/api.html#http-api-v2
    project_data = {
        "name": crate_name,
        "homepage": f"https://crates.io/crates/{crate_name}",
        "backend": "crates.io",
        "version_scheme": "semantic",
        "version_filter": "alpha;beta;rc;pre",
    }
    response = requests.post(
        "https://release-monitoring.org/api/v2/projects/",
        data=project_data,
        headers={"Authorization": f"token {api_key}"},
    )
    if response.status_code not in [200, 201, 409]:
        print(Colors.RED + "Failed to create project in Anitya" + Colors.RESET)
        print(response.text)
        print()
        return

    package_data = {
        "distribution": "Fedora",
        "package_name": f"rust-{crate_name}",
        "project_name": project_data["name"],
        "project_ecosystem": project_data["backend"],
    }
    response = requests.post(
        "https://release-monitoring.org/api/v2/packages/",
        data=package_data,
        headers={"Authorization": f"token {api_key}"},
    )
    if response.status_code not in [200, 201, 409]:
        print(Colors.RED + "Failed to create package in Anitya" + Colors.RESET)
        print(response.json().get("error", ""))
        print()
        return

    print(Colors.GREEN + "Package is now being monitored by Anitya" + Colors.RESET)


def rust_sig_access(package_name: str, api_key: str):
    """Give 'rust-sig' group access to the pagure repository

    Parameters:
        package_name: Package name which permissions should be altered
        api_key: API key that should be used for authentication
    """
    # https://pagure.io/api/0/#general-tab
    response = requests.post(
        f"https://src.fedoraproject.org/api/0/rpms/{package_name}/git/modifyacls",
        data={
            "user_type": "group",
            "name": "rust-sig",
            "acl": "commit",
        },
        headers={"Authorization": f"token {api_key}"},
    )
    if response.status_code != 200:
        print(Colors.RED + "Failed to give rust-sig 'commit' access" + Colors.RESET)
        print(response.text)
        print()
        return

    print(Colors.GREEN + "'rust-sig' has commit access to repository" + Colors.RESET)


def make(args: Namespace):
    crate_name = (
        args.package_name[5:]
        if args.package_name.startswith("rust-")
        else args.package_name
    )

    config = Config().command_config(args.command)
    monitor_package(crate_name, config.get("anitya_api_key", ""))
    rust_sig_access(args.package_name, config.get("pagure_api_key", ""))
