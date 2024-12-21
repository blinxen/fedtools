import glob
import os
from argparse import Namespace
from fedtools.utils import exec_cmd, LOGGER
from fedtools.config import Config


DEFAULT_MOCK_ROOT_DIR = os.path.abspath("./mock-root")
DEFAULT_MOCK_RESULT_DIR = os.path.abspath("./mock-result")


def get_srpm_file_name(path: str) -> str:
    srpm_path = ""
    for line in path.split("\n"):
        if line.startswith("Wrote"):
            srpm_path = line.split(":")[1].strip()
            break

    if not os.path.exists(srpm_path):
        LOGGER.error("Could not parse SRPM file name from rpmbuild output")
        exit(1)

    return os.path.basename(srpm_path)


def download_source(path: str):
    exec_cmd(
        "spectool",
        ["--get-files", path],
        error_msg="ERROR: spectool could not download the source file!",
    )


def build_srpm_with_fedpkg(arch: str) -> str:
    cmd_arguments = ["srpm"]
    if arch is not None:
        cmd_arguments.append("--arch")
        cmd_arguments.append(arch)

    result = exec_cmd(
        "fedpkg",
        cmd_arguments,
        error_msg="ERROR: rpmbuild could not build the SRPM!",
    )

    return get_srpm_file_name(result.stdout.decode("utf-8"))


def build_binary_rpm_with_mock(srpm_path: str, mock_arguments: list[str]):
    mock_arguments.append(srpm_path)
    exec_cmd("mock", mock_arguments, tail_command=True)

    LOGGER.info("Running rpmlint")
    # Run RPM lint on the built RPMs
    for path in glob.glob(f"{DEFAULT_MOCK_RESULT_DIR}/*.rpm"):
        if "src.rpm" in path:
            continue

        LOGGER.info(path)
        exec_cmd("rpmlint", [path], tail_command=True)


def build(args: Namespace):
    download_source(args.specfile)
    srpm_path = build_srpm_with_fedpkg(args.arch)

    if args.mock is True:
        config = Config().command_config(args.command)
        mock_arguments = config.get("mock-arguments", [])
        if "--resultdir" not in mock_arguments:
            mock_arguments.append("--resultdir")
            mock_arguments.append(DEFAULT_MOCK_RESULT_DIR)
        if "--rootdir" not in mock_arguments:
            mock_arguments.append("--rootdir")
            mock_arguments.append(DEFAULT_MOCK_ROOT_DIR)
        build_binary_rpm_with_mock(
            srpm_path,
            mock_arguments,
        )
