import subprocess
import sys
import os
from subprocess import CompletedProcess
from pathlib import Path
import json


FEDTOOLS_CONFIG_FILE = os.path.join(Path.home(), ".config/fedtools.conf")


class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    WHITE = "\033[37m"
    RESET = "\033[0m"


def __pretty_print_subprocess_result(msg, result):
    print(msg)
    print()
    print("----------------------STDOUT-------------------------")
    print(result.stdout.decode("utf-8"))
    print("-----------------------------------------------------")
    print()
    print("---------------------STDERR--------------------------")
    print(result.stderr.decode("utf-8"))
    print("-----------------------------------------------------")


def exec_cmd(
    cmd: str,
    cmd_arguments: list[str],
    subprocess_arguments: dict = None,
    tail_command: bool = False,
    check_result: bool = True,
    error_msg: str = "",
) -> CompletedProcess:
    """Execute a command with subprocess.

    Parameters:
        cmd: Command to execture.
        cmd_arguments: Arguments that will be passed with the command.
        subprocess_arguments: Arguments that are specific to subprocess.
        tail_command: Whether print the command stdout and stderr to the command line.
                      If this is set to True then `check_result` is ignored.
        check_result: Whether to check the result of the executed command or not.
                      This will exit the program if it is set to True and the return
                      code of the command is unequal to 0.
                      This argument will be ignored if `tail_command` is set to True.
        error_msg: Error message if the executed command fails.
                   This will be used when `check_result` is set to True.
    """

    # Workaround for having a dict for subprocess_arguments as the default value
    # See: https://stackoverflow.com/a/67480279/8511820
    if subprocess_arguments is None:
        subprocess_arguments = {}

    # Build command that we want to execute
    final_cmd = [cmd]
    final_cmd.extend(cmd_arguments)

    # Build the subprocess arguments that should be passed
    if tail_command is True:
        subprocess_arguments["stdout"] = sys.stdout
        subprocess_arguments["stderr"] = sys.stderr
    elif check_result is True:
        subprocess_arguments["capture_output"] = True

    # Execute command with the defined options
    result = subprocess.run(final_cmd, **subprocess_arguments)

    if tail_command is False and check_result is True and result.returncode != 0:
        __pretty_print_subprocess_result(error_msg, result)
        exit(1)

    return result


def anitya_api_key() -> str:
    api_key = None
    with open(FEDTOOLS_CONFIG_FILE, "r") as f:
        api_key = json.load(f).get("anitya_api_key", None)

    if api_key is None or len(api_key) == 0:
        print(f"Anitya api key is not declared in {FEDTOOLS_CONFIG_FILE}!!")
        exit(1)

    return api_key


def pagure_api_key() -> str:
    api_key = None
    with open(FEDTOOLS_CONFIG_FILE, "r") as f:
        api_key = json.load(f).get("pagure_api_key", None)

    if api_key is None or len(api_key) == 0:
        print(f"Pagure api key is not declared in {FEDTOOLS_CONFIG_FILE}!!")
        exit(1)

    return api_key
