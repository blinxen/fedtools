import glob
import os
from argparse import Namespace
from fedtools.utils import exec_cmd


def get_srpm_file_name(path: str) -> str:
    srpm_path = ""
    for line in path.split("\n"):
        if line.startswith("Wrote"):
            srpm_path = line.split(":")[1].strip()
            break

    if not os.path.exists(srpm_path):
        print("ERROR: Could not parse SRPM file name from rpmbuild output")
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


def build_binary_rpm_with_mock(srpm_path: str, mock_root: str):
    exec_cmd(
        "mock", ["--postinstall", "--root", mock_root, srpm_path], tail_command=True
    )

    print()
    print("Running rpmlint")
    print()
    # Run RPM lint on the built RPMs
    for path in glob.glob(f"/var/lib/mock/{mock_root}/result/*.rpm"):
        if "src.rpm" in path:
            continue

        print()
        print(path)
        exec_cmd("rpmlint", [path], tail_command=True)


def build(args: Namespace):
    download_source(args.specfile)
    srpm_path = build_srpm_with_fedpkg(args.arch)

    if args.mock is True:
        build_binary_rpm_with_mock(srpm_path, args.mock_root)
