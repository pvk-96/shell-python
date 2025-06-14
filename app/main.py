import sys
import os
import subprocess
import shlex


def main():

    sys.stdout.write("$ ")

    # Wait for user input
    command = input()

    if ">" in command or "1>" in command or "2>" in command:
        os.system(command)
    elif command == "exit 0":
        exit(0)
    elif command.startswith("echo "):
        args = shlex.split(command[5:])
        print(" ".join(args))
    elif command.strip() == "pwd":
        print(os.getcwd())
    elif command.strip().startswith("cd"):
        parts = command.strip().split(maxsplit=1)
        if len(parts) == 1 or not parts[1]:
            pass
        else:
            path = os.path.expanduser(parts[1])
            try:
                os.chdir(path)
            except FileNotFoundError:
                print(f"cd: {path}: No such file or directory")
    elif command.startswith("type "):
        cmd_name = command[5:]
        if cmd_name == "echo":
            print("echo is a shell builtin")
        elif cmd_name == "exit":
            print("exit is a shell builtin")
        elif cmd_name == "type":
            print(f"type is a shell builtin")
        elif cmd_name == "pwd":
            print("pwd is a shell builtin")
        elif cmd_name == "cd":
            print("cd is a shell builtin")
        else:
            # Search for the command in the PATH
            found = False
            for path in os.environ.get("PATH", "").split(os.pathsep):
                full_path = os.path.join(path, cmd_name)
                if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                    print(f"{cmd_name} is {full_path}")
                    found = True
                    break
            if not found:
                print(f"{cmd_name}: not found")

    else:
        parts = shlex.split(command.strip())
        if not parts:
            main()
            return
        cmd_name = parts[0]
        args = parts[1:]
        found = False
        for path in os.environ.get("PATH", "").split(os.pathsep):
            full_path = os.path.join(path, cmd_name)
            if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                try:
                    result = subprocess.run(
                        [cmd_name] + args, executable=full_path, check=False
                    )
                except Exception as e:
                    print(f"{cmd_name}: failed to execute")
                found = True
                break
        if not found:
            print(f"{cmd_name}: command not found")

    main()


if __name__ == "__main__":
    main()