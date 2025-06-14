import os
import readline
import shlex
import subprocess
import sys
from contextlib import contextmanager, ExitStack


# ---------------------- Debug Utilities ----------------------
def print_debug(message: str) -> None:
    """Print debug messages when DEBUG environment variable is set."""
    if environment["DEBUG"]:
        print(f"[DEBUG] {message}")


# ---------------------- PATH Handling ----------------------
def search_path(path: str) -> None:
    """Recursively search PATH for executables."""
    print_debug(f"Searching for executables in PATH: {path}")
    for directory in path.split(":"):
        if os.path.isdir(directory):
            for file in os.listdir(directory):
                file_abs = os.path.join(directory, file)
                if os.path.isfile(file_abs):
                    path_executables.append([file, {file_abs}])
                else:
                    if os.path.isdir(file):
                        print_debug(f"Scanning sub-directory: {file_abs}")
                        search_path({file_abs})
    print_debug(f"Found {len(path_executables)} executables in PATH")


def get_absolute_path(app: str) -> str | None:
    """Find absolute path of an executable in PATH."""
    app_path = None
    for executable in path_executables:
        if app in executable:
            print_debug(f"Found executable {app} in {executable}")
            app_path = "".join(executable[1])
        if app_path is not None:
            return app_path
    return None


# -------------------- Builtin Functions --------------------
def get_builtin_function(app: str) -> str | None:
    """Check if command is a shell builtin."""
    app_path = None
    if app in shell_builtins:
        print_debug(f"Found executable {app} in shell-builtins")
        app_path = shell_builtins[app]
    return app_path if app_path is not None else None


# ------------------- Environment Handling -------------------
def get_environment_value(key: str = None) -> None:
    """Read environment variables from OS."""
    if key is None:
        print("No key provided. Nothing to do.")
        return
    environment[key] = os.getenv(key)
    print_debug(f"Saved value for {key}: {environment[key]}")


# ------------------ Builtin Implementations ------------------
def shell_builtin_echo(args: list) -> None:
    """Echo command implementation."""
    print(" ".join(args))


def shell_builtin_exit(exit_code: list) -> None:
    """Exit command implementation."""
    if len(exit_code) > 1:
        print(f"exit: Invalid number of arguments. Expected 1, given {len(exit_code)}")
    elif not exit_code:
        sys.exit(0)
    else:
        sys.exit(int("".join(exit_code)))


def shell_builtin_type(args: list) -> None:
    """Type command implementation."""
    if len(args) != 1:
        print(f"type: Invalid number of arguments. Expected 1, given {len(args)}")
        return

    command = "".join(args)
    if command in shell_builtins:
        print(f"{command} is a shell builtin")
    else:
        exec_path = get_absolute_path(command)
        print(f"{command} is {exec_path}" if exec_path else f"{command}: not found")


def shell_builtin_pwd(args: list = None) -> str:
    """PWD command implementation."""
    current_dir = os.getcwd()
    if not args:
        print(current_dir)
    return current_dir


def shell_builtin_cd(args: list) -> None:
    """CD command implementation."""
    if len(args) != 1:
        print(f"cd: Invalid number of arguments. Expected 1, given {len(args)}")
        return

    target_dir = args[0]
    print_debug(f"Changing directory to {target_dir}")

    # Handle tilde expansion
    if target_dir.startswith("~"):
        print_debug(f"Tilde detected. Replacing with {environment['HOME']}")
        target_dir = target_dir.replace("~", environment["HOME"])

    # Handle relative paths
    if not os.path.isabs(target_dir):
        print_debug(f"Relative path detected. Prefixing with cwd.")
        target_dir = os.path.join(shell_builtin_pwd(True), target_dir)

    # Validate and change directory
    if os.path.exists(target_dir):
        if os.path.isdir(target_dir):
            print_debug(f"Changing cwd to {target_dir}")
            os.chdir(target_dir)
        else:
            print(f"cd: {target_dir}: Cannot cd into a file")
    else:
        print(f"cd: {target_dir}: No such file or directory")


# -------------------- Process Execution --------------------
def launch_executable(command: str, args: list = None) -> tuple[str, str]:
    """Execute external command and capture output."""
    print_debug(f"Launching executable {command}. Arguments: {args}")
    command_list = [command]
    if args:
        command_list.extend(args)

    result = subprocess.run(
        command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    return result.stdout, result.stderr


# ------------------- Output Redirection -------------------
@contextmanager
def redirect_stdout(new_target):
    """Context manager for stdout redirection."""
    original_stdout = sys.stdout
    sys.stdout = new_target
    try:
        yield
    finally:
        sys.stdout = original_stdout


@contextmanager
def redirect_stderr(new_target):
    """Context manager for stderr redirection."""
    original_stderr = sys.stderr
    sys.stderr = new_target
    try:
        yield
    finally:
        sys.stderr = original_stderr


# ---------------------- Main Execution Logic ----------------------
def execute_command(command: str, arguments: list) -> None:
    """Unified command execution logic."""
    if builtin := get_builtin_function(command):
        print_debug(f"Launching {command}")
        shell_builtins[command](arguments)
    elif get_absolute_path(command):
        print_debug(f"Found {command}. Executing.")
        stdout, stderr = launch_executable(command, arguments)
        if stdout:
            print(stdout.strip())
        if stderr:
            print(stderr.strip(), file=sys.stderr)
    else:
        print(f"{command}: command not found")


# -------------------- Auto Completion --------------------
def completer(text: str, state: int) -> str | None:
    """Tab completion for builtin commands."""
    matches = [cmd + " " for cmd in shell_builtins if cmd.startswith(text)]
    return matches[state] if state < len(matches) else None


# ---------------------- Main Shell Loop ----------------------
def main() -> None:
    """Main shell program loop."""
    # Initialize environment
    get_environment_value("DEBUG")
    get_environment_value("PATH")
    get_environment_value("HOME")
    search_path(environment["PATH"])

    # Setup tab completion
    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")

    while True:
        try:
            # Read input
            sys.stdout.write("$ ")
            command = input().strip()

            if not command:
                continue

            # Parse command and arguments
            parts = shlex.split(command)
            if not parts:
                continue

            command, *arguments = parts
            stdout_info = None
            stderr_info = None
            redirection_indices = set()

            # Find all redirections
            for i, arg in enumerate(arguments):
                # Check for append first
                if ">>" in arg:
                    parts = arg.split(">>", 1)
                    stream_part = parts[0] or "1"
                    file_part = parts[1] if len(parts) > 1 else ""
                    mode = "a"
                elif ">" in arg:
                    parts = arg.split(">", 1)
                    stream_part = parts[0] or "1"
                    file_part = parts[1] if len(parts) > 1 else ""
                    mode = "w"
                else:
                    continue

                # Validate stream type
                if stream_part not in ("1", "2"):
                    print(f"Invalid stream: {stream_part}")
                    continue

                # Get output filename
                if file_part:
                    output_file = file_part
                    redirection_indices.add(i)
                else:
                    if i + 1 < len(arguments):
                        output_file = arguments[i + 1]
                        redirection_indices.update({i, i + 1})
                    else:
                        print("Error: No output file specified")
                        continue

                # Store redirection info
                if stream_part == "1":
                    stdout_info = (output_file, mode)
                else:
                    stderr_info = (output_file, mode)

            # Filter out redirection arguments
            arguments = [
                arg for i, arg in enumerate(arguments) if i not in redirection_indices
            ]

            # Prepare context managers
            contexts = []
            files = []

            # Handle stdout redirection
            if stdout_info:
                filename, mode = stdout_info
                f_stdout = open(filename, mode)
                files.append(f_stdout)
                contexts.append(redirect_stdout(f_stdout))

            # Handle stderr redirection
            if stderr_info:
                filename, mode = stderr_info
                f_stderr = open(filename, mode)
                files.append(f_stderr)
                contexts.append(redirect_stderr(f_stderr))

            # Execute command with context managers
            with ExitStack() as stack:
                for ctx in contexts:
                    stack.enter_context(ctx)

                if contexts:
                    execute_command(command, arguments)
                    # Explicitly close files after execution
                    for f in files:
                        f.close()
                else:
                    execute_command(command, arguments)

        except Exception as e:
            print(f"Error: {str(e)}")


# ---------------------- Data Structures ----------------------
shell_builtins = {
    "exit": shell_builtin_exit,
    "echo": shell_builtin_echo,
    "type": shell_builtin_type,
    "pwd": shell_builtin_pwd,
    "cd": shell_builtin_cd,
}

path_executables = []
environment = {}

if __name__ == "__main__":
    main()