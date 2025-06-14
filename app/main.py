import shutil
import sys
import os

BUILTINS = ["exit", "echo", "type", "pwd", "cd"]


def type(cmd):
    if cmd in BUILTINS:
        print(f"{cmd} is a shell builtin")
    elif path := shutil.which(cmd):
        print(f"{cmd} is {path}")
    else:
        print(f"{cmd}: not found")


def main():
    sys.stdout.write("$ ")

    command = input()
    cmd, *args = command.split()

    if cmd == "exit" and args[0] == "0":
        return 0
    elif cmd == "echo":
        print(" ".join(args))
    elif cmd == "type":
        type(args[0])
    elif cmd == "pwd":
        print(os.getcwd())
    elif cmd == "cd":

        try:
            os.chdir(" ".join(args))
        except:
            print(f"{cmd}: {' '.join(args)}: No such file or directory")
    elif path := shutil.which(cmd):
        os.system(f"{cmd} {' '.join(args)}")
    else:
        print(f"{cmd}: command not found")

    main()


if __name__ == "__main__":
    main()