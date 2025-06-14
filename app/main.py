import sys
import os
import subprocess
import shlex


def find_in_path(command):
    for path in os.environ.get("PATH", "").split(":"):
        full_path = os.path.join(path, command)
        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            return full_path
    return None


def cd_command(*args):
    if not args:
        target_dir = os.path.expanduser("~")
    else:
        path = args[0]
        target_dir = os.path.expanduser(path)
        target_dir = os.path.abspath(target_dir)

    try:
        os.chdir(target_dir)
    except FileNotFoundError:
        print(f"cd: {target_dir}: No such file or directory")
    except NotADirectoryError:
        print(f"cd: {target_dir}: Not a directory")
    except PermissionError:
        print(f"cd: {target_dir}: Permission denied")


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
    "cd": cd_command,
}


def main():
    try:
        while True:
            sys.stdout.write("$ ")
            sys.stdout.flush()
            command_with_args = shlex.split(input())

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
