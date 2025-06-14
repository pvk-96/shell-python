import sys
import os
import subprocess


def is_executable_file(filename: str):
    paths = os.environ["PATH"].split(":")
    for path in paths:
        full_path = os.path.join(path, filename)
        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            return full_path
    return False


def tokenize(command):
    tokens = []
    current = ""
    in_single = False
    in_double = False
    escape = False

    for ch in command:
        if escape:
            current += ch
            escape = False
            continue

        if ch == "\\" and not in_double:
            escape = True
            continue

        if in_single:
            if ch == "'":
                in_single = False
            else:
                current += ch
            continue

        if in_double:
            if ch == '"':
                in_double = False
            else:
                current += ch
            continue

        if ch == "'":
            in_single = True
            continue

        if ch == '"':
            in_double = True
            continue

        if ch.isspace():
            if current:
                tokens.append(current)
                current = ""
            continue

        current += ch

    if current:
        tokens.append(current)

    return tokens


def main():
    working_directory = os.getcwd()

    while True:
        sys.stdout.write("$ ")

        # Wait for user input
        command = input()
        if command.strip() == "exit 0":
            break
        elif command.startswith("echo"):
            value = command.replace("echo ", "")
            print(" ".join(tokenize(value)))
        elif command == "pwd":
            print(working_directory)
        elif command.startswith("cat"):
            subprocess.run(tokenize(command))
        elif command.startswith("cd"):
            path = command.replace("cd ", "")
            if path.strip() == "~":
                working_directory = os.path.expanduser("~")
            elif os.path.exists(path) and os.path.isabs(path):
                working_directory = path
            elif os.path.exists(ful_path := os.path.join(working_directory, path)):
                working_directory = os.path.normpath(ful_path)
            else:
                print(f"cd: {path}: No such file or directory")
        elif command.startswith("type"):
            args = command.replace("type ", "")
            if args in ("echo", "exit", "type", "pwd"):
                print(f"{args} is a shell builtin")
            elif full_path := is_executable_file(args):
                print(f"{args} is {full_path}")
            else:
                print(f"{args}: not found")
        elif is_executable_file(command.split(" ")[0]):
            subprocess.run(command.split(" "))
        else:
            print(f"{command}: command not found")


if __name__ == "__main__":
    main()