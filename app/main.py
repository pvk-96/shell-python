import sys
import shutil


def echo(command):
    echoed_command = command[5:]
    print(echoed_command)


def invalid(command):
    print(f"{command}: command not found")


def type(command):
    types = ["echo", "exit", "type"]
    if command[5:] in types:
        print(f"{command[5:]} is a shell builtin")
    elif path := shutil.which(command[5:]):
        print(f"{command[5:]} is {path}")
    else:
        print(f"{command[5:]}: not found")


def main():
    true = 1
    while true:
        sys.stdout.write("$ ")
        command = input()

        if command == "exit 0":
            true = 0
        elif command[:5] == "echo ":
            echo(command)
        elif command[:5] == "type ":
            type(command)
        else:
            invalid(command)


if __name__ == "__main__":
    main()