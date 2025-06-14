import sys

BUILTINS = {
    "exit": lambda code=0, *_: sys.exit(int(code)),
    "echo": lambda *args: print(" ".join(args)),
    "type": lambda cmd, *_: print(f"{cmd} is a shell builtin")
    if cmd in BUILTINS
    else print(f"{cmd}: not found"),
}


def main():
    while True:
        sys.stdout.write("$ ")
        sys.stdout.flush()

        usr_input = input().split()
        cmd = usr_input[0]
        args = usr_input[1:]
        if cmd in BUILTINS:
            BUILTINS[cmd](*args)
        else:
            print(f"{cmd}: command not found")


if __name__ == "__main__":
    main()