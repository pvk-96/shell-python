import os
import sys
import shutil
import subprocess


def main():
    # Wait for user input
    built_ins = ["exit", "echo", "type", "pwd", "cd"]
    while True:
        sys.stdout.write("$ ")
        command = input().strip()
        match command.split():
            case ["exit", status]:
                sys.exit(int(status))
            case ["echo", *args]:
                print(" ".join(args))
            case ["pwd"]:
                print(os.getcwd())
            case ["type", cmd]:
                if cmd in built_ins:
                    print(f"{cmd} is a shell builtin")
                elif path := shutil.which(cmd):
                    print(f"{cmd} is {path}")
                else:
                    print(f"{cmd}: not found")
            case ["cd", path]:
                try:
                    path = os.path.expanduser(path)
                    os.chdir(path)
                except (FileNotFoundError, NotADirectoryError):
                    print(f"cd: {path}: No such file or directory")
            case [cmd, *args]:
                if shutil.which(cmd):
                    subprocess.run([cmd] + args)
                else:
                    print(f"{command}: command not found")
            case _:
                print(f"{command}: command not found")


if __name__ == "__main__":
    main()