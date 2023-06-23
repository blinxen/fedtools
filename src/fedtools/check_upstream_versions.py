import glob
import os
from urllib.parse import urlparse
import requests
import re
import tabulate
from argparse import Namespace
from fedtools.utils import exec_cmd, Colors


# Expressions inspired by
# https://github.com/bkircher/python-rpm-spec/blob/61a4107a39ffffc58a47bbdf729fe2184b920647/pyrpm/spec.py#L254
NAME_TAG = re.compile(r"^Name\s*:\s*(\S+)", re.IGNORECASE)
SOURCE_TAG = re.compile(r"^Source0?\s*:\s*(.+)", re.IGNORECASE)
VERSION_TAG = re.compile(r"^Version\s*:\s*(\S+)", re.IGNORECASE)
# RUST_NAME_TAG and IS_RUST_PACKAGE are not needed anymore
# but are kept for completeness
# RUST_NAME_TAG = re.compile(r"^%global\s+crate\s+(\S+)")
# Currently only one source tag is supported
# According to https://docs.fedoraproject.org/en-US/packaging-guidelines/Rust/
# all rust packages MUST have rust-packaging as a build dependency
# IS_RUST_PACKAGE = re.compile(r"BuildRequires\s*:\s*rust-packaging.*")
# Re-uses tcp sessions, should make program faster
requests_session = requests.Session()
adapter = requests.adapters.HTTPAdapter(max_retries=10)
requests_session.mount("https://", adapter)
requests_session.mount("http://", adapter)
# Version prefixes that can exist in upstream
VERION_PREFIXES = ["v"]


def http_get(url: str) -> requests.Response:
    user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
    return requests_session.get(
        url, allow_redirects=True, headers={"User-Agent": user_agent}
    )


def gather_package_information(path: str) -> list[dict]:
    packages = []
    # Iterate over all found spec files
    for path in glob.glob(os.path.join(path, "*/*.spec")):
        # Name of the package
        name = None
        # Current version of the pacakge
        version = None
        # Source of the package
        source = None

        result = exec_cmd(
            "rpmspec",
            ["-P", path],
            check_result=False,
            subprocess_arguments={"capture_output": True},
        )
        if result.returncode != 0:
            print(f"Error processing {path}")
            continue

        content = result.stdout.decode("utf-8")
        # Iterate over all line and get the needed information
        for line in content.split("\n"):
            if match := NAME_TAG.match(line):
                name = match.group(1)
            elif match := SOURCE_TAG.match(line):
                source = match.group(1)
            elif match := VERSION_TAG.match(line):
                version = match.group(1)

        if name is None or version is None or source is None:
            print(f"WARNING: Could not parse {path} correctly!")
            continue

        packages.append(
            {
                "name": name,
                "source": source,
                "version": version,
            }
        )

    return packages


def get_latest_package_version(package: dict) -> str:
    latest_version = None

    if urlparse(package["source"]).netloc == "crates.io":
        # https://crates.io/api/v1/crates/<crate_name>
        if package["name"].startswith("rust-"):
            package_name = package["name"][5:]
        else:
            package_name = package["name"]

        # This is the case when the package name
        # differs from the crate name
        # Example: libimagequant
        if package_name not in package["source"]:
            # Here we assume that the crate source
            # has the format: https://crates.io/api/v1/crates/%name/%version/download#/%name-%version.crate
            package_name = (
                package["source"]
                .split("https://crates.io/api/v1/crates/")[1]
                .split("/")[0]
            )

        repsonse = http_get(f"https://crates.io/api/v1/crates/{package_name}")

        if repsonse.status_code != 200:
            print(f"Could not fetch crate information for {package_name}")
            print(f"REASON: {repsonse.text}")
            return
        else:
            repsonse = repsonse.json()

        if "crate" not in repsonse:
            print(f"WARNING: Could not determine the latest version of {package_name}")
            return
        latest_version = repsonse["crate"].get("newest_version", None)
    elif (source := urlparse(package["source"])).netloc == "github.com":
        # [1:] --> ignore first slash in the path
        url_path = source.path[1:].split("/")
        if url_path[2] in ("archive", "releases"):
            # https://github.com/<user>/<proj>/archive/<tag>/<file>
            # https://github.com/<user>/<proj>/releases/download/<tag>/<file>
            project_path = f"{url_path[0]}/{url_path[1]}"
        elif url_path[0] == "downloads":
            project_path = f"{url_path[1]}/{url_path[2]}"

        latest_version = (
            http_get(f"https://api.github.com/repos/{project_path}/tags")
            .json()[0]
            .get("name", None)
        )
    elif "gitlab" in (source := urlparse(package["source"])).netloc:
        # [1:] --> ignore first slash in the path
        project_path = source.path[1:].split("/-/")
        if len(project_path) != 2:
            # https://gitlab.<...>.org/<user>/<proj>/archive/<tag>/<file>
            print("WARNING: Gitlab urls without /-/ are currently not supported")
            return
        else:
            # https://gitlab.<...>.org/<user>/<proj>/-/archive/<tag>/<file>
            #
            # Get the project name from the project path
            # This is normally the last string in the path
            project_name = project_path[0].split("/")[-1]
            project_id = http_get(
                f"https://{source.netloc}/api/v4/projects?search={project_name}"
            ).json()
            # We want to make sure that we got the right project
            # if the search was not clear, then we cannot assume
            # that we got the right project
            if len(project_id) == 0 or len(project_id) > 1:
                return
            else:
                project_id = project_id[0].get("id")

        latest_version = (
            http_get(
                f"https://{source.netloc}/api/v4/projects/{project_id}/repository/tags?order_by=updated&sort=desc"
            )
            .json()[0]
            .get("name", None)
        )
    elif (source := urlparse(package["source"])).netloc in (
        "files.pythonhosted.org",
        "pypi.python.org",
        "pypi.org",
    ):
        # https://files.pythonhosted.org/packages/source/<P>/<Package>/<File>
        # https://pypi.python.org/packages/source/<P>/<Package>/<File>
        # https://pypi.org/packages/source/<P>/<Package>/<File>
        # [1:] --> ignore first slash in the path
        project_name = source.path[1:].split("/")[3]
        latest_version = http_get(f"https://pypi.org/pypi/{project_name}/json").json()[
            "info"
        ]["version"]

    return latest_version


def generate_tabulate_list(packages: list) -> list[list]:
    """Generate the list that will be used as the tabulate input

    Returns:
        list[list]: Formated list with all packages that need to be updated
    """
    tabulate_list = []
    for package in packages:
        if package["latest_version"] is None:
            color = Colors.RED
            package["latest_version"] = "-"
        elif compare_two_versions(package["version"], package["latest_version"]):
            color = Colors.GREEN
        else:
            color = Colors.YELLOW

        tabulate_list.append(
            [
                color + package["name"] + Colors.RESET,
                color + package["version"] + Colors.RESET,
                color + package["latest_version"] + Colors.RESET,
                color + package["source"] + Colors.RESET,
            ]
        )

    return tabulate_list


def compare_two_versions(version1: str, version2: str) -> bool:
    """Compare two version strings and return True if they match
    Ignore possible prefixes

    Returns:
        bool: Whether the versions match or not
    """

    for prefix in VERION_PREFIXES:
        if version1.startswith(prefix) and not version2.startswith(prefix):
            version2 = f"{prefix}{version2}"
            break
        elif version2.startswith(prefix) and not version1.startswith(prefix):
            version1 = f"{prefix}{version1}"
            break

    return version1 == version2


def check_versions(args: Namespace):
    packages = gather_package_information(args.path)
    if not packages:
        print("No packages were found!!")
        exit(1)

    updatable_packages = []
    for package in packages:
        package["latest_version"] = get_latest_package_version(package)
        updatable_packages.append(package)
    # Sort packages
    updatable_packages.sort(
        key=lambda package: package["latest_version"] == package["version"],
        reverse=True,
    )
    updatable_packages.sort(
        key=lambda package: package["latest_version"] is None, reverse=True
    )
    if updatable_packages:
        print(
            tabulate.tabulate(
                generate_tabulate_list(updatable_packages),
                headers=["Name", "Version", "Latest version", "Source"],
                tablefmt="simple_grid",
            )
        )
