import sys
import os
import subprocess
import shlex
import readline

SHELL_BUILTIN_COMMANDS = [
    "echo",
    "exit",
    "type",
    "pwd",
    "cd",
    "history",
]


def is_builtin_command(command):
    """
    Check if the command is a built-in shell command.
    """
    return command in SHELL_BUILTIN_COMMANDS


PATH = os.environ.get("PATH", "").split(os.pathsep)
HOME = os.environ.get("HOME", "")


def handle_type_command(commands):
    exec_path = is_command_in_path(commands[1])
    if is_builtin_command(commands[1]):
        print(f"{commands[1]} is a shell builtin")
    elif exec_path:
        print(f"{commands[1]} is {exec_path}")
    else:
        print(f"{commands[1]}: not found")


def execute_pipeline_commands(commands):
    """Execute a pipeline and optionally capture the final output"""
    processes = []
    prev_pipe = None

    for i, cmd in enumerate(commands):
        cmd_parts = shlex.split(cmd)
        if not cmd_parts:
            continue

        # For the last command, decide where output goes
        if i == len(commands) - 1:
            # Last command - capture output or send to stdout
            stdout = sys.stdout
            pipe_read, pipe_write = None, None
        else:
            # Intermediate command - create pipe
            pipe_read, pipe_write = os.pipe()
            stdout = pipe_write

        if cmd_parts[0] == "type":
            handle_type_command(cmd_parts)
            continue

        process = subprocess.Popen(
            cmd_parts, stdin=prev_pipe, stdout=stdout, stderr=subprocess.PIPE
        )

        processes.append(process)

        # Close file descriptors
        if prev_pipe:
            os.close(prev_pipe)
        if pipe_write:
            os.close(pipe_write)

        prev_pipe = pipe_read
    for p in processes:
        p.wait()


def is_command_in_path(command):
    """
    Check if the command is in the system PATH.
    """
    for directory in PATH:
        if os.path.isfile(os.path.join(directory, command)):
            return os.path.join(directory, command)
    return False


def completer(test, state):
    """
    A simple tab completer for the shell.
    It completes commands and file paths based on the current input.
    """
    options = [cmd for cmd in SHELL_BUILTIN_COMMANDS if cmd.startswith(test)]
    # read PATH directories for executable files
    if not options:
        for directory in PATH:
            try:
                files = os.listdir(directory)
                options.extend(
                    [
                        f
                        for f in files
                        if f.startswith(test)
                        and os.access(os.path.join(directory, f), os.X_OK)
                    ]
                )
            except FileNotFoundError:
                continue
    if len(options) > 1:
        return f"{options[state]}" if state < len(options) else None
    else:
        return f"{options[state]} " if state < len(options) else None


readline.set_completer(completer)
readline.parse_and_bind("tab: complete")
# readline.parse_and_bind('bind ^I rl_complete')


def main():
    while True:
        # Wait for user input
        command = input("$ ")
        if "|" in command:
            execute_pipeline_commands(command.split("|"))
            continue
        commands = shlex.split(command)
        mode = "w"
        out_file = None
        err_file = None
        if (
            ">" in commands
            or "1>" in commands
            or "2>" in commands
            or ">>" in commands
            or "2>>" in commands
            or "1>>" in commands
        ):
            index = 0
            if "2>>" in commands:
                index = commands.index("2>>")
                mode = "a"
                err_file = commands[index + 1]
            elif "1>>" in commands:
                index = commands.index("1>>")
                mode = "a"
                out_file = commands[index + 1]
            elif ">>" in commands:
                index = commands.index(">>")
                mode = "a"
                out_file = commands[index + 1]
            elif "2>" in commands:
                index = commands.index("2>")
                err_file = commands[index + 1]
            elif "1>" in commands:
                index = commands.index("1>")
                out_file = commands[index + 1]
            elif ">" in commands:
                index = commands.index(">")
                out_file = commands[index + 1]
            if index + 1 < len(commands):
                commands = commands[:index]
        if commands[0] == "exit" and commands[1] == "0":
            sys.exit(0)
        elif commands[0] == "type":
            handle_type_command(commands)
        elif commands[0] == "pwd":
            print(os.getcwd())
        elif commands[0] == "cd":
            if os.path.isdir(commands[1]):
                os.chdir(commands[1])
            elif commands[1] == "~":
                os.chdir(HOME)
            else:
                print(f"{commands[0]}: {commands[1]}: No such file or directory")
        else:
            exec_path = is_command_in_path(commands[0])
            if exec_path:
                if out_file:
                    os.makedirs(os.path.dirname(out_file), exist_ok=True)
                    with open(out_file, mode) as f:
                        subprocess.run(commands, stdout=f, text=True)
                elif err_file:
                    os.makedirs(os.path.dirname(err_file), exist_ok=True)
                    with open(err_file, mode) as f:
                        subprocess.run(commands, stderr=f, text=True)
                else:
                    subprocess.run(commands)
            else:
                print(f"{command}: command not found")


if __name__ == "__main__":
    main()