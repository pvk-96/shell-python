import sys
import os
import subprocess
import shlex
import readline
import io

history_list = []


def get_common_prefix(strings):
    if not strings:
        return ""
    shortest = min(strings, key=len)
    for i, char in enumerate(shortest):
        for other in strings:
            if other[i] != char:
                return shortest[:i]
    return shortest


def autocomplete(text, state):
    """Autocomplete function for command line input."""
    builtins = ["echo", "exit", "pwd", "cd", "type"]

    path_executables = set()
    for dir in os.environ.get("PATH", "").split(os.pathsep):
        if not os.path.isdir(dir):
            continue
        try:
            for file_name in os.listdir(dir):
                full_path = os.path.join(dir, file_name)
                if os.access(full_path, os.X_OK):
                    path_executables.add(file_name)
        except Exception:
            continue

    options = []
    seen = set()
    for cmd in builtins + list(path_executables) + os.listdir("."):
        if cmd.startswith(text) and cmd not in seen:
            options.append(cmd)
            seen.add(cmd)
    options.sort()

    if not options:
        return None

    if len(options) == 1:
        if state == 0:
            return options[0] + " "
        return None

    common = get_common_prefix(options)

    if len(common) > len(text):
        if state == 0:
            return common
        return None

    if state == 0:
        sys.stdout.write("\a")
        sys.stdout.flush()
        return text
    elif state == 1:
        print()
        print("  ".join(options))
        sys.stdout.write("$ " + readline.get_line_buffer())
        sys.stdout.flush()
        return text

    return None


def show_prompt():
    """Show the shell prompt."""
    sys.stdout.write("$ ")
    sys.stdout.flush()


readline.set_auto_history(False)
readline.parse_and_bind("set editing-mode emacs")
readline.parse_and_bind("set horizontal-scroll-mode off")
# readline.set_pre_input_hook(show_prompt)
readline.set_completer(autocomplete)
readline.parse_and_bind("tab: complete")


def is_builtin(cmd):
    return cmd in ["echo", "exit", "pwd", "cd", "type"]


def run_builtin(cmd_parts, stdin_data=None):
    # Redirect sys.stdin if needed
    old_stdin = sys.stdin
    if stdin_data is not None:
        sys.stdin = io.StringIO(stdin_data)
    output = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = output
    try:
        if cmd_parts[0] == "echo":
            print(" ".join(cmd_parts[1:]))
        elif cmd_parts[0] == "pwd":
            print(os.getcwd())
        elif cmd_parts[0] == "type":
            for name in cmd_parts[1:]:
                if name in ["echo", "exit", "pwd", "cd", "type"]:
                    print(f"{name} is a shell builtin")
                else:
                    found = False
                    for path in os.environ.get("PATH", "").split(os.pathsep):
                        full_path = os.path.join(path, name)
                        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                            print(f"{name} is {full_path}")
                            found = True
                            break
                    if not found:
                        print(f"{name}: not found")
        # Add more built-ins as needed
    finally:
        sys.stdout = old_stdout
        sys.stdin = old_stdin
    return output.getvalue()


def execute_pipeline(command_line):
    stages = [stage.strip() for stage in command_line.split("|")]
    num_stages = len(stages)
    processes = []
    prev_output = None

    for i, stage in enumerate(stages):
        cmd_parts = shlex.split(stage)
        is_last = i == num_stages - 1

        if is_builtin(cmd_parts[0]):
            # Built-in: run and pass output as string
            output = run_builtin(cmd_parts, stdin_data=prev_output)
            prev_output = output
        else:
            # External command
            if prev_output is not None:
                # Previous output is from a built-in, pass as input
                p = subprocess.Popen(
                    cmd_parts,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE if not is_last else None,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                out, err = p.communicate(input=prev_output)
                if not is_last:
                    prev_output = out
                else:
                    if out:
                        print(out, end="")
                    if err:
                        print(err, end="", file=sys.stderr)
                processes.append(p)
            else:
                # Previous output is from an external, chain pipes
                if not processes:
                    # First external command
                    p = subprocess.Popen(
                        cmd_parts,
                        stdout=subprocess.PIPE if not is_last else None,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                else:
                    # Chain: stdin from previous process
                    p = subprocess.Popen(
                        cmd_parts,
                        stdin=processes[-1].stdout,
                        stdout=subprocess.PIPE if not is_last else None,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                    processes[-1].stdout.close()
                processes.append(p)
                if is_last:
                    # Stream output from last process
                    try:
                        while True:
                            line = p.stdout.readline()
                            if not line:
                                break
                            sys.stdout.write(line)
                            sys.stdout.flush()
                    except Exception:
                        pass
                    if p.stdout:
                        p.stdout.close()

    # If the last stage was a built-in, print its output
    if is_builtin(shlex.split(stages[-1])[0]):
        if prev_output:
            print(prev_output, end="")

    # Wait for all external processes
    for p in processes:
        try:
            p.wait()
        except Exception:
            pass


def main():
    while True:
        try:
            command = input("$ ")
        except EOFError:
            break  # Exit on Ctrl-D

        if not command.strip():
            continue

        history_list.append(command)
        readline.add_history(command)

        if "|" in command:
            execute_pipeline(command)
        elif (
            ">" in command
            or "1>" in command
            or "2>" in command
            or "1>>" in command
            or "2>>" in command
        ):
            os.system(command)
        elif command == "exit 0":
            exit(0)
        elif command.startswith("echo "):
            args = shlex.split(command[5:])
            print(" ".join(args))
        elif command.strip() == "pwd":
            print(os.getcwd())
        elif command.strip().startswith("history"):
            parts = command.strip().split()
            if len(parts) == 2 and parts[1].isdigit():
                n = int(parts[1])
                start = max(len(history_list) - n, 0)
                for idx, cmd in enumerate(history_list[start:], start + 1):
                    print(f"{idx}  {cmd}")
            else:
                for idx, cmd in enumerate(history_list, 1):
                    print(f"{idx}  {cmd}")
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
            elif cmd_name == "history":
                print("history is a shell builtin")
            else:
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
                continue
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


if __name__ == "__main__":
    main()