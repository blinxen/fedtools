from argparse import Namespace

from copr.v3 import Client
import os
import tomllib
import glob

from fedtools.utils import create_copr_repo, LOGGER, copr_build, package_name_from_srpm


def load_config(path: str) -> dict:
    config = {}
    with open(path, "rb") as f:
        try:
            config = tomllib.load(f)
        except tomllib.TOMLDecodeError:
            LOGGER.error("Configuration file has an invalid format")
            exit(1)

    return config


def check_copr_repository(client: Client, config: dict):
    if not config.get("repository") and not config.get("build-order"):
        LOGGER.error(
            '"repository" or "build-order" are not defined in the configuration file'
        )
        exit(1)

    create_copr_repo(client, config["repository"])

    return config["repository"]


def parse_build_order(config: dict) -> list[list[str]]:
    build_order = []
    error = False

    for build in config.get("build-order", []):
        if error:
            break

        if not config.get(build):
            error = True
            LOGGER.error(f"{build} is defined in build-order but is not configured")
        elif not config[build].get("packages"):
            error = True
            LOGGER.error(f"Packages list is not defined for {build}")
        elif config[build].get("packages"):
            packages = []
            for package in config[build].get("packages"):
                if not os.path.exists(package) or not glob.glob(
                    os.path.join(package, "*.src.rpm")
                ):
                    error = True
                    LOGGER.error(
                        f"Path for package {package} does not exist or SRPM file is missing"
                    )
                    break
                else:
                    srpm = glob.glob(os.path.join(package, "*.src.rpm"))

                    if "src.rpm" in package:
                        packages.append(package)
                    elif len(srpm) == 1:
                        packages.append(srpm[0])
                    elif len(srpm) > 1:
                        error = True
                        LOGGER.error(
                            f"Too many SRPM files are present in {package}.\n"
                            "Either delete all except one or specify the full path to the SRPM"
                        )
                        break
                    else:
                        error = True
                        LOGGER.error(f"Unexpected error for {package}")
                        break

            build_order.append(packages)

    if error:
        exit(1)

    return build_order


def chain_build(client: Client, repository: str, build_order: list[list[str]]):
    previous_build_id = None

    for build in build_order:
        options = {}
        if previous_build_id is not None:
            options = {"after_build_id": previous_build_id}

        # Start the first build and get its ID
        # With this ID we will combine the remaining packages with this build
        current_build_id = copr_build(client, repository, build[0], buildopts=options)
        previous_build_id = current_build_id
        options = {"with_build_id": current_build_id}

        # Start building the remaining packages
        for package in build[1:]:
            copr_build(client, repository, package, buildopts=options)


def print_fedpkg_chain_build_command(build_order: list[list[str]]):
    command = "fedpkg chain-build --target=<PUT_SIDE_TAG_HERE> \\\n"
    for build in build_order[:-1]:
        command += "    "
        for package in build:
            command += f"{package_name_from_srpm(package)} "
        command += ": \\\n"

    # Add last step
    command += "    "
    for package in build_order[-1]:
        command += f"{package_name_from_srpm(package)} "

    print(command)


def build(args: Namespace):
    client = Client.create_from_config_file()
    if not os.path.exists(args.config_toml):
        LOGGER.error(f"Config file {args.config_toml} does not exist")
        exit(1)

    config = load_config(args.config_toml)
    if config.get("build-directory") and os.path.exists(config["build-directory"]):
        os.chdir(config["build-directory"])

    repository = check_copr_repository(client, config)
    build_order = parse_build_order(config)

    if args.generate_fedpkg_command:
        print_fedpkg_chain_build_command(build_order)
        exit(0)

    chain_build(client, repository, build_order)
