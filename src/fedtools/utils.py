import subprocess
import sys
from subprocess import CompletedProcess
from typing import Callable


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
        tail_command: Whether to print the command stdout and stderr to the command line.
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


def check_value_of_key_in_list_of_dicts(
    key: str, value: str, dicts_list: list[dict]
) -> bool:
    """Check whether a specific key-value pair in a list of dicts exists

    Parameters:
        key: Dictionary key that should be used to retrieve the value
        value: Value that we are checking
        dicts_list: List of dictionaries that will be iterated over

    Returns: Boolean that indicates whether they key-value pairs exists or not
    """
    return value in list(map(lambda item: item.get(key, None), dicts_list))


def search_for_dict_in_list_of_dicts_and_get_value(
    key: str,
    predicate: Callable,
    dicts_list: list[dict],
) -> str | None:
    """Search for a specifc dict in list of dicts with `predicate` and return a value from it

    Parameters:
        key: Dictionary key that should be used to retrieve the value after the dictionary has been found
        predicate: Lambda function that will be used to filter `dicts_list`
        dicts_list: List of dictionaries that will be iterated over

    Returns: This either returns the value that we are looking for or None
    """
    try:
        return next(filter(predicate, dicts_list)).get(key, None)
    except StopIteration:
        return None
