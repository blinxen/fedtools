import glob
import os
import subprocess
import shutil
from argparse import Namespace


def pretty_print_subprocess_result(msg, subprocess_result):
    print(msg)
    print()
    print("----------------------STDOUT-------------------------")
    print(subprocess_result.stdout.decode("utf-8"))
    print("-----------------------------------------------------")
    print()
    print("---------------------STDERR--------------------------")
    print(subprocess_result.stderr.decode("utf-8"))
    print("-----------------------------------------------------")


def get_srpm_file_name(path: str) -> str:
    for line in path.split("\n"):
        if line.startswith("Wrote"):
            srpm_path = line.split(":")[1].strip()
            break

    if not os.path.exists(srpm_path):
        print("ERROR: Could not parse SRPM file name from rpmbuild output")
        exit(1)

    return os.path.basename(srpm_path)


def download_source(path: str):
    result = subprocess.run(
        ["spectool", "--get-files", path], capture_output=True
    )
    if result.returncode != 0:
        pretty_print_subprocess_result(
            "ERROR: spectool could not download the source file!", result
        )
        exit(1)


def build_srpm_with_fedpkg(arch: str) -> str:
    command = ["fedpkg", "srpm"]
    if arch is not None:
        command.append("--arch")
        command.append(arch)

    result = subprocess.run(command, capture_output=True)
    if result.returncode != 0:
        pretty_print_subprocess_result(
            "ERROR: rpmbuild could not build the SRPM!", result
        )
        exit(1)

    return get_srpm_file_name(result.stdout.decode("utf-8"))


def build_binary_rpm_with_mock(srpm_path: str, mock_root: str):
    import sys

    subprocess.run(
        ["mock", "--root", mock_root, srpm_path],
        stdout=sys.stdout,
        stderr=sys.stderr,
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

        subprocess.run(
            ["rpmlint", path],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )


def build(args: Namespace):
    download_source(args.specfile)
    srpm_path = build_srpm_with_fedpkg(args.arch)

    if args.mock is True:
        build_binary_rpm_with_mock(srpm_path, args.mock_root)
