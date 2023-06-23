from argparse import Namespace
import requests
from fedtools.utils import anitya_api_key, pagure_api_key, Colors


def monitor_package(crate_name: str, api_key: str):
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


def track_builds(package_name: str):
    # No public API available
    #
    print(Colors.YELLOW + "Add package to koschei manually!!" + Colors.RESET)


def rust_sig_access(package_name: str, api_key: str):
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
    monitor_package(crate_name, anitya_api_key())
    track_builds(args.package_name)
    rust_sig_access(args.package_name, pagure_api_key())
