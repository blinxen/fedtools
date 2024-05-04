import glob
import os
from urllib.parse import urlparse
import requests
import re
import tabulate
from argparse import Namespace
from fedtools.config import Config
from fedtools.utils import (
    exec_cmd,
    Colors,
    check_value_of_key_in_list_of_dicts,
    search_for_dict_in_list_of_dicts_and_get_value,
)
import git


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
                # This is used to get the state of the git directory
                "git_path": os.path.dirname(os.path.abspath(path)),
            }
        )

    return packages


def lookup_version_by_prefix(versions: list, raw_prefix: str) -> str | None:
    # Differentiate between prefixes and (not) prefixes
    # prefixes are used to only consider versions that start with them
    # (not) prefixes are used to ignore versions that start with them
    if raw_prefix.startswith("!"):
        prefix = raw_prefix[1:]
    else:
        prefix = raw_prefix

    # We assume versions is already sorted from latest to oldest versions
    for version in versions:
        if raw_prefix.startswith("!"):
            if version.startswith(prefix):
                continue
            else:
                return version
        else:
            if version.startswith(prefix):
                return version

    return None


def get_latest_package_version(package: dict, config: dict) -> str | None:
    latest_version = None

    if urlparse(package["source"]).netloc == "crates.io":
        # https://crates.io/api/v1/crates/<crate_name>
        if package["name"].startswith("rust-"):
            crate_name = package["name"][5:]
        else:
            crate_name = package["name"]

        # This is the case when the package name
        # differs from the crate name
        # Example: libimagequant
        if crate_name not in package["source"]:
            # Here we assume that the crate source
            # has the format: https://crates.io/api/v1/crates/%name/%version/download#/%name-%version.crate
            crate_name = (
                package["source"]
                .split("https://crates.io/api/v1/crates/")[1]
                .split("/")[0]
            )

        response = http_get(f"https://crates.io/api/v1/crates/{crate_name}")

        if response.status_code != 200:
            print(f"Could not fetch crate information for {crate_name}")
            print(f"REASON: {response.text}")
            return
        else:
            response = response.json()

        if "crate" not in response:
            print(f"WARNING: Could not determine the latest version of {crate_name}")
            return
        latest_version = response["crate"].get("max_version", None)
    elif (source := urlparse(package["source"])).netloc == "github.com":
        # [1:] --> ignore first slash in the path
        url_path = source.path[1:].split("/")
        if url_path[2] in ("archive", "releases"):
            # https://github.com/<user>/<proj>/archive/<tag>/<file>
            # https://github.com/<user>/<proj>/releases/download/<tag>/<file>
            project_org = url_path[0]
            project_name = url_path[1]
        elif url_path[0] == "downloads":
            project_org = url_path[1]
            project_name = url_path[2]
        else:
            print("Unsupported source URL for GitHub!!")
            return

        response = http_get(
            f"https://api.github.com/repos/{project_org}/{project_name}/tags"
        ).json()
        if response is dict and "API rate limit exceeded" in response.get(
            "message", ""
        ):
            return None
        # Check whether we have to look for a specific version prefix
        if check_value_of_key_in_list_of_dicts(
            "name", project_name, config["upstream-version-prefix"]
        ):
            latest_version = lookup_version_by_prefix(
                list(map(lambda version: version["name"], response)),
                search_for_dict_in_list_of_dicts_and_get_value(
                    "prefix",
                    lambda item: item.get("name") == project_name,
                    config["upstream-version-prefix"],
                ),
            )
        else:
            latest_version = response[0].get("name", None)
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

        response = http_get(
            f"https://{source.netloc}/api/v4/projects/{project_id}/repository/tags?order_by=updated&sort=desc"
        ).json()
        # Check whether we have to look for a specific version prefix
        if check_value_of_key_in_list_of_dicts(
            "name", project_name, config["upstream-version-prefix"]
        ):
            latest_version = lookup_version_by_prefix(
                list(map(lambda version: version["name"], response)),
                search_for_dict_in_list_of_dicts_and_get_value(
                    "prefix",
                    lambda item: item.get("name") == project_name,
                    config["upstream-version-prefix"],
                ),
            )
        else:
            latest_version = response[0].get("name", None)
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


def generate_tabulate_list(packages: list, version_prefixes: list[str]) -> list[list]:
    """Generate the list that will be used as the tabulate input

    Parameters:
        packages: List of packages that will be displayed
        version_prefixes: Version prefixes that will be forwarded to the compare_two_versions
                          function.

    Returns: Formated list with all packages that need to be updated
    """
    tabulate_list = []
    for package in packages:
        git_dirty = " (dirty)" if git.Repo(package["git_path"]).is_dirty() else ""
        if package["latest_version"] is None:
            color = Colors.RED
            package["latest_version"] = "-"
        elif compare_two_versions(
            package["version"], package["latest_version"], version_prefixes
        ):
            color = Colors.GREEN
        else:
            color = Colors.YELLOW

        tabulate_list.append(
            [
                color + package["name"] + git_dirty + Colors.RESET,
                color + package["version"] + Colors.RESET,
                color + package["latest_version"] + Colors.RESET,
                color + package["source"] + Colors.RESET,
            ]
        )

    return tabulate_list


def compare_two_versions(
    version1: str, version2: str, version_prefixes: list[str]
) -> bool:
    """Compare two version strings and return True if they match
    Ignore possible prefixes

    Parameters:
        version1 / version2: Versions that should be compared
        version_prefixes: List of version prefix that should be tried. In some cases
                          upstream uses diffrent version names, such a "v" or "v1".

    Returns: Boolean that indicates whether the versions match or not
    """

    for prefix in version_prefixes:
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
    config = Config().command_config(args.command)

    for package in packages:
        package["latest_version"] = get_latest_package_version(package, config)
        updatable_packages.append(package)

    tabulate_list = generate_tabulate_list(
        updatable_packages, config.get("version-prefix", [])
    )
    # Sort packages
    tabulate_list.sort(
        key=lambda package: Colors.YELLOW in package[0],
    )
    tabulate_list.sort(
        key=lambda package: Colors.RED in package[0],
    )
    if updatable_packages:
        print(
            tabulate.tabulate(
                tabulate_list,
                headers=["Name", "Version", "Latest version", "Source"],
                tablefmt="simple_grid",
            )
        )
