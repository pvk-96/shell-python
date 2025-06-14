import sys
import shutil
import subprocess
import os


def main():
    # Uncomment this block to pass the first stage
    builtins = {
        "echo": "echo is a shell builtin",
        "exit": "exit is a shell builtin",
        "type": "type is a shell builtin",
        "pwd": "pwd is a shell builtin",
    }

    while True:
        sys.stdout.write("$ ")
        if command := input().strip():
            match command.split():

                # buildins commands
                case ["echo", *args]:
                    print(" ".join(args))

                case ["exit", status]:
                    sys.exit(int(status))

                case ["type", cmd]:
                    path = shutil.which(cmd)

                    if cmd in builtins:
                        print(f"{builtins[cmd]}")
                    elif path:
                        print(f"{cmd} is {path}")
                    else:
                        print(f"{cmd}: not found")

                case ["cd", dir]:
                    try:
                        os.chdir(dir)
                    except FileNotFoundError:
                        print(f"cd: {dir}: No such file or directory")

                case ["pwd"]:
                    print(os.getcwd())

                # external commands
                case [cmd, *args]:
                    path = shutil.which(cmd)
                    if path:
                        try:
                            subprocess.run([cmd] + args)

                        except subprocess.CalledProcessError as e:
                            print(e)

                    else:
                        print(f"{command}: not found")

                case _:
                    print(f"{command}: not found")


if __name__ == "__main__":
    main()