import sys
import os
import subprocess
from functools import partial


def parse_any(parsers, s):
    for parser in parsers:
        res, remaining = parser(s)
        if res:
            return res, remaining
    return None, s


def parse_char(c, s):
    if len(s) == 0:
        return None, s
    else:
        if s[0] == c:
            return c, s[1:]
        else:
            return None, s[1:]


def parse_whitespace(s):
    return parse_any(
        [
            parse_char(),
        ]
    )


def parse_word_char(s):
    if len(s) > 0:
        if s[0] in [""]:
            result = s[0]
    if len(s) > 1:
        remaining = s[1:]
    return result, remaining


def parse_word(s):
    i = 0
    while i < len(s) and s[i] != " ":
        i += 1
    _, r = parse_whitespaces(s[i:])
    return s[:i], r


def parse_simple_quotes(s):
    if s[0] == "'":
        i = 1
        while i < len(s) and s[i] != "'":
            i += 1
        _, r = parse_whitespaces(s[i:])
        return s[:i], r
    else:
        return ("", s)


def main():
    shell_builtin = ["exit", "echo", "type", "pwd"]

    paths = os.getenv("PATH").split(":")

    executables = {}
    for dir in paths:
        if os.path.isdir(dir):
            for file in os.listdir(dir):
                if file not in executables and os.path.isfile(os.path.join(dir, file)):
                    executables[file] = os.path.join(dir, file)

    while True:
        # Uncomment this block to pass the first stage
        sys.stdout.write("$ ")

        # Wait for user input
        input_str = input()

        # Split user input
        cmd = []
        cur_arg = ""
        it = iter(input_str)
        try:
            c = next(it)
            while True:
                if c == "'":
                    c = next(it)
                    while c != "'":
                        cur_arg += c
                        c = next(it)
                    c = next(it)

                elif c == '"':
                    c = next(it)
                    while c != '"':
                        if c == "\\":
                            c = next(it)
                            if c in '\\$"':
                                cur_arg += c
                                c = next(it)
                            else:
                                cur_arg += "\\"
                        else:
                            cur_arg += c
                            c = next(it)
                    c = next(it)

                elif c == "\\":
                    c = next(it)
                    cur_arg += c
                    c = next(it)

                elif c == " ":
                    cmd.append(cur_arg)
                    cur_arg = ""
                    while c == " ":
                        c = next(it)

                else:
                    cur_arg += c
                    c = next(it)

        except StopIteration:
            cmd.append(cur_arg)

        # Run command
        match cmd:
            case ["exit", code]:
                sys.exit(int(code))
            case ["pwd"]:
                print(os.getcwd())
            case ["cd", path]:
                if path[0] == "~":
                    path = os.path.normpath(os.getenv("HOME") + "/" + path[1:])
                if os.path.isdir(path):
                    os.chdir(path)
                else:
                    print(f"cd: {path}: No such file or directory")
            case ["echo", *args]:
                print(" ".join(args))
            case ["type", cmd2]:
                if cmd2 in shell_builtin:
                    print(f"{cmd2} is a shell builtin")
                elif cmd2 in executables:
                    print(f"{cmd2} is {executables[cmd2]}")
                else:
                    print(f"{cmd2}: not found")
            case [cmd, *args] if cmd in executables:
                subprocess.run([cmd] + args)
            case [cmd, *args]:
                print(f"{cmd}: command not found")


if __name__ == "__main__":
    main()