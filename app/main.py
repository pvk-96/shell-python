import sys
import os
import subprocess
import shlex

from pathlib import Path
from itertools import takewhile
from dataclasses import dataclass

cmd_library = {
    "echo": "echo is a shell builtin",
    "exit": "exit is a shell builtin",
    "pwd": "pwd is a shell builtin",
    "type": "type is a shell builtin",
}


@dataclass
class Response:
    """Response structure from commands"""

    stdout: str
    stderr: str


def get_executable_path(cmd):
    path_dirs = os.getenv("PATH").split(":")
    for bin_dir in path_dirs:
        if os.path.isdir(bin_dir):
            if cmd in os.listdir(bin_dir):
                return os.path.join(bin_dir, cmd)

    return None


def run_subprocess(cmd, args=None, output=False):
    return subprocess.run(
        [cmd, *args] if args else [cmd],
        capture_output=output,
        encoding="UTF-8",
        text=True,
    )


def handle_cd(args, redirect_errors):
    try:
        home = os.getenv("HOME")
        if "~" in args[0]:
            return os.chdir(args[0].replace("~", home))
        return os.chdir(args[0])
    except FileNotFoundError:
        if redirect_errors:
            return Response("", f"cd: {args[0]}: No such file or directory")
        return f"cd: {args[0]}: No such file or directory"


def command_parser(
    cmd: str, args: list = None, redirect_out=False, redirect_errors=False
):
    if cmd == "exit":
        sys.exit()

    executable_path = get_executable_path(cmd)

    if cmd == "echo":
        return " ".join(args)

    if cmd == "pwd":
        return os.getcwd()

    if cmd == "cd":
        return handle_cd(args, redirect_errors)

    if executable_path:
        output = run_subprocess(cmd, args or None, redirect_out)
        if output.stderr and not redirect_errors:
            sys.stdout.write(output.stderr)

        if redirect_errors:
            return output

        return output.stdout if redirect_out else None

    if cmd == "type":
        doc = cmd_library.get(args[0])
        if doc:
            return doc

        executable_path = get_executable_path(args[0])
        if executable_path:
            return executable_path

        return f"{args[0]}: not found"

    return f"{cmd}: command not found"


def clean_args(args):
    return [arg.replace("'", "") for arg in args]


def parse_arguments(commands):
    # returns a command set
    cmd_set = shlex.split(commands)
    if len(cmd_set) == 1:
        return commands, None

    cmd = cmd_set[0]
    args = cmd_set[1:]
    return cmd, args


def check_or_create_file(filename):
    if os.path.exists(filename):
        return True

    file = Path(filename)
    file.parent.mkdir(parents=True, exist_ok=True)
    return True


def main():
    # Uncomment this block to pass the first stage
    sys.stdout.write("$ ")
    sys.stdout.flush()

    # Wait for user input
    to_file = False
    the_file = ""
    redirect_errors = False
    mode = ""
    command = input()
    cmd_set = parse_arguments(command)
    args = cmd_set[1]
    response = None
    if args:
        redirect = list(
            set(args)
            & {
                ">>",
                "1>>",
                "2>>",
                ">",
                "1>",
                "2>",
            }
        )
        if len(redirect) > 0:
            redirect_errors = True if "2>" in redirect[0] else False
            mode = "a" if ">>" in redirect[0] else "w"
            to_file = True
            the_file = cmd_set[1][-1]
            check_or_create_file(the_file)
            args = list(takewhile(lambda x: ">" not in x, args))

    response = command_parser(
        cmd_set[0], args, redirect_out=to_file, redirect_errors=redirect_errors
    )

    if not to_file:
        if response:
            print(response)
            sys.stdout.flush()
        else:
            sys.stdout.flush()
    else:
        if redirect_errors:
            if hasattr(response, "stderr"):
                if response.stdout != "":
                    print(response.stdout.rstrip("\n"))
                response = response.stderr
            else:
                print(response)
                sys.stdout.flush()
                response = None

        if response:
            with open(the_file, mode) as f:
                if response.endswith("\n"):
                    f.writelines(response)
                else:
                    f.writelines(response + "\n")
        else:
            with open(the_file, mode="a"):
                pass


if __name__ == "__main__":
    while True:
        main()