import argparse
import os
import pathlib
import shutil

import nltk
from dotenv import load_dotenv

from .tui import run_tui

REQUIRED_ENV_VARS = ["GITHUB_USERNAME", "WRITE_PATH", "PL_QUESTION_PATH", "MY_NAME", "MY_INITIALS"]
_REQ_VARS_TEXT = ", ".join(f"{var!r}" for var in REQUIRED_ENV_VARS[:-1]) + f", and {REQUIRED_ENV_VARS[-1]!r}"


class _Formatter(argparse.HelpFormatter):
    def __init__(self, prog: str) -> None:
        width = shutil.get_terminal_size().columns
        super().__init__(prog, max_help_position=32, width=min(120, width - 2))


def main():
    parser = argparse.ArgumentParser(
        prog="OPB Question Creator",
        formatter_class=_Formatter,
        description=(
            "Create a barebones OPB markdown question via a series of tui prompts."
            + "It requires the following environment variables to be set, either via '--env-file',"
            + f"or in the shell's environment: {_REQ_VARS_TEXT}"
        ),
        epilog=(
            "This program requires both 'git' and 'gh' to be installed to create PRs."
            + "You can find the installation instructions for 'gh' at https://github.com/cli/cli#installation."
        ),
    )
    parser.add_argument(
        "--create-pr",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Create a PR with the generated question.",
    )
    parser.add_argument(
        "--gpt",
        action="store_true",
        help=(
            "Use ChatGPT gpt-3.5-turbo to generate the MCQ options and number input code. "
            + "If this is specified, the environment variable 'OPENAI_API_KEY' is also required "
            + "to be available, or be in the env file specified by --env-file. (default: %(default)s)"
        ),
    )
    env_file = parser.add_mutually_exclusive_group()
    env_file.add_argument(
        "--env-file",
        action="store",
        default=".env",
        help="Path to the environment file with the required environment variables (default: %(default)s)",
    )
    env_file.add_argument(
        "--no-env-file",
        action="store_false",
        help=(
            "Do read from any environment file. "
            + "If you use this, make sure the required environment variables are set in your shell's environment.  (default: False)"
        ),
    )
    args = parser.parse_args()

    CREATE_PR = args.create_pr
    USE_GPT = args.gpt

    if args.no_env_file:
        ENV_FILE = pathlib.Path(args.env_file).expanduser().resolve()
        print(f"Loading environment variables from '{ENV_FILE}'.")
        load_dotenv(ENV_FILE)

    if USE_GPT and "OPENAI_API_KEY" not in os.environ:
        parser.error("The 'OPENAI_API_KEY' environment variable is required when using the --gpt flag.")

    if CREATE_PR and shutil.which("gh") is None:
        parser.error(
            "The 'gh' command is required to create a PR. "
            + "Please install it following the instructions at https://github.com/cli/cli#installation"
        )

    if CREATE_PR and shutil.which("git") is None:
        parser.error("The 'git' command is required to create a PR. Please install it.")

    for var in REQUIRED_ENV_VARS:
        if var not in os.environ:
            parser.error(
                f"The environment variable {var!r} is required."
                + "Please set it in your shell's environment or in the specified environment file."
            )

    nltk.download("punkt", quiet=True)
    nltk.download("stopwords", quiet=True)
    nltk.download("wordnet", quiet=True)

    return run_tui(create_pr=CREATE_PR, use_gpt=USE_GPT) or 0


if __name__ == "__main__":
    raise SystemExit(main())
