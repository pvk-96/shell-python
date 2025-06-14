import sys
import os
import subprocess


def find_in_path(command):
    for path in os.environ.get("PATH", "").split(":"):
        full_path = os.path.join(path, command)
        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            return full_path
    return None


def type_command(*args):
    global path
    for cmd in args:
        if cmd in commands:
            print(f"{cmd} is a shell builtin")
        else:
            path = find_in_path(cmd)
            if path:
                print(f"{cmd} is {path}")
            else:
                print(f"{cmd}: not found")


commands = {
    "exit": lambda exit_code: os._exit(int(exit_code)),
    "echo": lambda *args: print(" ".join(args)),
    "type": type_command,
    "pwd": lambda: print(os.getcwd()),
}


def main():
    try:
        while True:
            sys.stdout.write("$ ")
            sys.stdout.flush()
            command_with_args = input().split()

            command = command_with_args[0]
            args = command_with_args[1:]

            if command in commands:
                commands[command](*args)
            else:
                path = find_in_path(command)
                if path:
                    try:
                        subprocess.run([command] + args, executable=path)
                    except Exception as e:
                        print(f"Error executing {command}: {e}")
                else:
                    print(f"{command}: command not found")

    except KeyboardInterrupt:
        print("\nExiting...")


if __name__ == "__main__":
    main()
