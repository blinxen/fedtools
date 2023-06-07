from argparse import Namespace
import requests
from re import Pattern
import re
import pathlib
import os
from fedtools.utils import exec_cmd


BUGZILLA_URL = "https://bugzilla.redhat.com"
PACKAGE_NAME_REGEX = re.compile(r"Review Request: ?(\S*) ? -")
SPEC_FILE_REGEX = re.compile(r"Spec URL: ?(.*) ?\n")
SRPM_FILE_REGEX = re.compile(r"SRPM URL: ?(.*) ?\n")
REVIEW_FILE_REGEX = re.compile(r"Review template:\n ?(.*) ?\n")


def ask_user(question: str) -> bool:
    yes_or_no = input(question)
    if yes_or_no.lower() not in ["y", "n", "yes", "no"]:
        print("Invalid input!!!\n")
        return ask_user(question)

    return yes_or_no.lower() in ["y", "yes"]


def download_file_from_comments(
    dest_file_path: str,
    regex: Pattern,
    comments: list[dict],
    comment_id: int,
    skip_question: bool,
) -> bool:
    for comment in comments:
        if comment["count"] == comment_id:
            if match := regex.findall(comment["text"]):
                if len(match) == 1 and (
                    skip_question is True
                    or ask_user(f"Do you want to download {match[0]}? (y/n)\n")
                ):
                    with open(dest_file_path, "wb") as f:
                        f.write(requests.get(match[0]).content)
                    return True
            break

    return False


def download_specfile(package_name: str, comments: list[dict], skip_question: bool):
    spec_file_path = os.path.join(package_name, package_name + ".spec")
    if (
        download_file_from_comments(
            spec_file_path, SPEC_FILE_REGEX, comments, 0, skip_question
        )
        is False
    ):
        print(f"Could not download spec file")
        exit(1)


def download_srpm(package_name: str, comments: list[dict], skip_question: bool):
    srpm_file_path = os.path.join(package_name, package_name + ".src.rpm")
    if (
        download_file_from_comments(
            srpm_file_path, SRPM_FILE_REGEX, comments, 0, skip_question
        )
        is False
    ):
        print(f"Could not download SRPM")
        exit(1)


def download_review_template(
    package_name: str, comments: list[dict], skip_question: bool
):
    review_file_path = os.path.join(package_name, "review.txt")
    if (
        download_file_from_comments(
            review_file_path, REVIEW_FILE_REGEX, comments, 1, skip_question
        )
        is False
    ):
        print("Could not download review.txt")


def create_directory(bug: dict) -> str:
    if match := PACKAGE_NAME_REGEX.match(bug["summary"]):
        package_name = match.group(1).strip()
    else:
        print("Cloud not determine the package name")
        exit(1)

    if re.fullmatch(r"[\-\_\Sa-zA-Z0-9]+", package_name) is not None:
        pathlib.Path(package_name).mkdir(exist_ok=True)
    else:
        print(f'Package name "{package_name}" is not valid')
        exit(1)

    return package_name


def make(args: Namespace):
    # Get bug and comments
    bug = requests.get(BUGZILLA_URL + "/rest/bug/" + args.bug).json()["bugs"][0]
    comments = requests.get(BUGZILLA_URL + "/rest/bug/" + args.bug + "/comment").json()[
        "bugs"
    ][args.bug]["comments"]
    # Create review directory where we will put everything we
    # need for the review
    package_name = create_directory(bug)
    # Download spec file and SRPM
    download_specfile(package_name, comments, args.y)
    download_srpm(package_name, comments, args.y)
    # Download review.txt
    download_review_template(package_name, comments, args.y)
    # Run rust2rpm if this is a rust package
    if package_name.startswith("rust-"):
        with open(os.path.join(package_name, "generated"), "w") as f:
            exec_cmd(
                "rust2rpm",
                ["--no-existence-check", "--stdout", package_name[5:]],
                check_result=False,
                subprocess_arguments={"stdout": f},
            )
