import os
import shutil
import sys
import shlex


def exit_command(command):
    func, code = command.split()
    return eval(func)(int(code))


def echo(command):
    parameters = shlex.split(command, posix=True)
    print(" ".join(parameters[1:]))


def error(command):
    print(f"{command}: not found")


def run_programme(command):
    args = shlex.split(command, posix=True)
    if shutil.which(args[0]):
        os.system(command)
        return
    return error(command)


def type_of(command):
    builtin = command.split()[1]
    if builtin in BUILTIN_FUNCTIONS.keys():
        print(f"{builtin} is a shell builtin")
        return
    if builtin_path := shutil.which(builtin):
        print(f"{builtin} is {builtin_path}")
        return
    error(builtin)


def pwd(_command):
    return print(os.getcwd())


def cd(command):
    nav_path = command.split()[1]
    os.path.expanduser(nav_path)
    if nav_path == "~":
        nav_path = os.environ["HOME"]
    try:
        os.chdir(nav_path)
    except FileNotFoundError:
        print(f"cd: {nav_path}: No such file or directory")


def command_matcher(command):
    if not command:
        return error
    function_str = command.split()[0]
    function = BUILTIN_FUNCTIONS.get(function_str)
    if not function:
        return run_programme
    return function


BUILTIN_FUNCTIONS = {
    "exit": exit_command,
    "echo": echo,
    "type": type_of,
    "pwd": pwd,
    "cd": cd,
}


def start():
    sys.stdout.write("$ ")

    command = input()
    command_matcher(command)(command)
    start()


def main():
    start()


if __name__ == "__main__":
    main()