import sys
import os


def raise_system_exit(exit_code):
    raise SystemExit(exit_code)


commands = {
    "exit": lambda exit_code: os._exit(int(exit_code)),
    "echo": lambda *args: print(" ".join(args)),
}


def main():
    while True:
        sys.stdout.write("$ ")
        sys.stdout.flush()

        # Wait for user input
        command_with_args = input().split()

        command = command_with_args[0]

        if not command in commands:
            print(f"{command}: command not found")
            continue

        commands[command](*command_with_args[1:])


if __name__ == "__main__":
    main()