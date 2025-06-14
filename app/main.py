import sys
import os
import subprocess
import readline  # type: ignore Keep this import to properly handle arrow keys in the input

from typing import Optional, Tuple, List, TextIO, Callable, Dict


class CommandError(Exception):
    def __init__(self, message: str):
        self.message = message

    def __repr__(self) -> str:
        return self.message


class UserInput:
    def __init__(
        self,
        input_parts: List[str],
        output_file: Optional[Tuple[str, bool]] = None,
        error_file: Optional[Tuple[str, bool]] = None,
    ):
        self.input_parts = input_parts
        self.output_file = output_file
        self.error_file = error_file

    def __repr__(self) -> str:
        return (
            f"UserInput(input_parts={self.input_parts}, "
            f"output_file={self.output_file}, "
            f"error_file={self.error_file})"
        )


class Command:
    def __init__(self, name: str):
        self.command_name = name
        self.out_stream: TextIO = sys.stdout
        self.err_stream: TextIO = sys.stderr
        self.in_stream: TextIO = sys.stdin

    def execute(self, params: List):
        pass

    def set_streams(
        self,
        out_stream: Optional[TextIO] = None,
        err_stream: Optional[TextIO] = None,
        in_stream: Optional[TextIO] = None,
    ):
        if out_stream:
            self.out_stream = out_stream

        if err_stream:
            self.err_stream = err_stream

        if in_stream:
            self.in_stream = in_stream

    def close_streams(self):
        if self.out_stream and self.out_stream != sys.stdout:
            self.out_stream.close()
            self.out_stream = sys.stdout

        if self.err_stream and self.err_stream != sys.stderr:
            self.err_stream.close()
            self.err_stream = sys.stderr

        if self.in_stream and self.in_stream != sys.stdin:
            self.in_stream.close()
            self.in_stream = sys.stdin


class PipeCommand(Command):
    def __init__(self, commands: List[Tuple[Command, List]]):
        super().__init__(" | ".join([cmd[0].command_name for cmd in commands]))
        self.commands = commands

    def execute(self, params: List):
        previous_pipe = None
        pids = []
        for i, (cmd, cmd_params) in enumerate(self.commands):
            current_pipe = None

            # Check if we need to create a pipe for the next command
            if i < len(self.commands) - 1:
                current_pipe = os.pipe()

            cmd_pid = os.fork()
            if cmd_pid == 0:
                # Child process
                # The pipe is a tuple (read_fd, write_fd)

                if current_pipe:
                    # If there is a current pipe (there is a next command), we only need the write end
                    os.close(current_pipe[0])
                    cmd.set_streams(out_stream=os.fdopen(current_pipe[1], "w"))

                if previous_pipe:
                    # We only need the read end of the previous pipe (if any)
                    os.close(previous_pipe[1])
                    cmd.set_streams(in_stream=os.fdopen(previous_pipe[0], "r"))

                cmd.execute(cmd_params)
                cmd.close_streams()

                os._exit(0)
                return

            # Parent process
            if previous_pipe:
                os.close(previous_pipe[0])
                os.close(previous_pipe[1])

            previous_pipe = current_pipe
            pids.append(cmd_pid)

        if previous_pipe:
            raise CommandError("There is a previous pipe that was not closed")

        for cmd_pid in pids:
            # Wait for the child processes to finish
            # We need to wait for all the child processes to avoid zombie processes
            # TODO handle the exit status of the child processes
            os.waitpid(cmd_pid, 0)

    def close_streams(self):
        for cmd, _ in self.commands:
            cmd.close_streams()


class CommandNotFound(Command):
    def __init__(self, command_name: str):
        super().__init__(command_name)

    def execute(self, params: List):
        print(f"{self.command_name}: command not found", file=self.err_stream)


class ExecutableCommand(Command):
    def __init__(self, path: str):
        super().__init__(os.path.basename(path))
        self.executable_path = path

    def execute(self, params: List):
        cmd = [self.command_name]
        cmd.extend(params)
        subprocess.run(
            cmd, stdout=self.out_stream, stderr=self.err_stream, stdin=self.in_stream
        )


class BuiltinCommand(Command):
    def __init__(self, name: str):
        super().__init__(name)


class ExitCommand(BuiltinCommand):
    NAME = "exit"

    def __init__(self):
        super().__init__(ExitCommand.NAME)

    def execute(self, params: List):
        hist_file = os.environ.get("HISTFILE")
        if hist_file and os.path.isfile(hist_file):
            # append history to file
            nelements = (
                readline.get_current_history_length() - history_items_loaded_on_startup
            )
            readline.append_history_file(nelements, hist_file)

        status_code = int(params[0]) if params else 0
        exit(status_code)


class EchoCommand(BuiltinCommand):
    NAME = "echo"

    def __init__(self):
        super().__init__(EchoCommand.NAME)

    def execute(self, params: List):
        if params:
            print(" ".join(params), file=self.out_stream)
        else:
            print(file=self.out_stream)


class TypeCommand(BuiltinCommand):
    NAME = "type"

    def __init__(self):
        super().__init__(TypeCommand.NAME)

    def execute(self, params: List):
        if not params:
            # Nothing to do
            return

        command_name = params[0]
        command = get_command(command_name)
        if isinstance(command, BuiltinCommand):
            print(f"{command_name} is a shell builtin", file=self.out_stream)
        elif isinstance(command, ExecutableCommand):
            print(f"{command_name} is {command.executable_path}", file=self.out_stream)
        else:
            print(f"{params[0]}: not found", file=self.err_stream)


class PwdCommand(BuiltinCommand):
    NAME = "pwd"

    def __init__(self):
        super().__init__(PwdCommand.NAME)

    def execute(self, params: List):
        print(os.getcwd(), file=self.out_stream)


class CdCommand(BuiltinCommand):
    NAME = "cd"

    def __init__(self):
        super().__init__(CdCommand.NAME)

    def execute(self, params: List):
        if not params:
            # TODO implement cd without params.
            pass

        # TODO For now, assuming only the path is provided in the arguments
        path_from_param = params[0]

        # TODO hanlde special cases like '-'

        # Use expandpath to handle special cases like '~'
        dest_path = os.path.expanduser(path_from_param)
        if os.path.isdir(dest_path):
            os.chdir(dest_path)
        elif os.path.isfile(dest_path):
            raise CommandError(f"{dest_path}: Not a directory")
        else:
            raise CommandError(f"{dest_path}: No such file or directory")


last_appended_history_index = 0


class HistoryCommand(BuiltinCommand):
    NAME = "history"

    def __init__(self):
        super().__init__(HistoryCommand.NAME)

    def execute(self, params: List):
        history_start = 0
        history_end = readline.get_current_history_length() + 1

        if params:
            if params[0] == "-r":
                filename = params[1]
                readline.read_history_file(filename)
                return

            if params[0] == "-w":
                filename = params[1]
                readline.write_history_file(filename)
                return

            if params[0] == "-a":
                global last_appended_history_index
                filename = params[1]
                nelements = (
                    readline.get_current_history_length() - last_appended_history_index
                )
                readline.append_history_file(nelements, filename)
                last_appended_history_index = readline.get_current_history_length()
                return

            if len(params) > 1:
                raise CommandError("Too many arguments")

            try:
                param = int(params[0])
                history_start = max(0, history_end - param)
            except ValueError:
                raise CommandError(f"{params[0]}: numeric argument is required")

        for i in range(history_start, history_end):
            history_item = readline.get_history_item(i)
            if history_item:
                print(f"\t{i}  {history_item}", file=self.out_stream)


BUILTIN_COMMANDS_FACTORY: Dict[str, Callable[[], BuiltinCommand]] = {
    ExitCommand.NAME: lambda: ExitCommand(),
    EchoCommand.NAME: lambda: EchoCommand(),
    TypeCommand.NAME: lambda: TypeCommand(),
    PwdCommand.NAME: lambda: PwdCommand(),
    CdCommand.NAME: lambda: CdCommand(),
    HistoryCommand.NAME: lambda: HistoryCommand(),
}


def find_in_path(program: str) -> Optional[str]:
    path_env = os.environ["PATH"].split(":")
    for path_entry in path_env:
        if os.path.isdir(path_entry):
            for path_file in os.listdir(path_entry):
                full_path_file = os.path.join(path_entry, path_file)
                if program == path_file and os.path.isfile(full_path_file):
                    return full_path_file
        elif os.path.isfile(path_entry) and program == os.path.basename(path_entry):
            return path_entry

    return None


def find_potential_files_in_path(prefix: str) -> List[str]:
    if not prefix:
        return []

    potential_files = set()  # Use a set to avoid duplicates
    path_env = os.environ["PATH"].split(":")
    for path_entry in path_env:
        if os.path.isdir(path_entry):
            for path_file in os.listdir(path_entry):
                full_path_file = os.path.join(path_entry, path_file)
                if path_file.startswith(prefix) and os.path.isfile(full_path_file):
                    potential_files.add(path_file)
        elif os.path.isfile(path_entry) and os.path.basename(path_entry).startswith(
            prefix
        ):
            potential_files.add(os.path.basename(path_entry))

    return list(potential_files)


def get_command(command_name: str) -> Command:
    # Check if it is a built-in command
    if command_name in BUILTIN_COMMANDS_FACTORY:
        return BUILTIN_COMMANDS_FACTORY[command_name]()

    executable_path = find_in_path(command_name)
    if executable_path:
        return ExecutableCommand(executable_path)

    return CommandNotFound(command_name)


def split_command(input_line: str) -> List[UserInput]:
    current_part = ""
    out_file = None
    err_file = None
    parts = []

    inside_squotes = False
    inside_dquotes = False

    is_reading_output_file = False
    is_reading_error_file = False
    is_append = False

    pipeline = []

    for i, c in enumerate(input_line):
        is_escaped = i > 0 and input_line[i - 1] == "\\"
        if i > 1:
            # The backslash is escaped if the previous character is not a backslash
            # and the character before that is not a backslash
            is_escaped = is_escaped and not input_line[i - 2] == "\\"

        if is_escaped:
            if inside_dquotes:
                # Double quotes preserves the special meaning of the backslash,
                # only when it is followed by \, $, " or newline
                if c not in ["\\", "$", '"', "\n"]:
                    current_part += "\\"
                    is_escaped = False

        if c == ">" and not inside_squotes and not inside_dquotes and not is_escaped:
            if input_line[i - 1] == ">":
                # Handle the append redirection '>>'
                is_append = True
                continue

            if current_part == "2":
                is_reading_error_file = True
                current_part = ""
            else:
                is_reading_output_file = True
                if current_part == "1":
                    # Handle the explicit redirection '1>'
                    current_part = ""

            # Save the input as an input part so far, before the redirection
            if current_part:
                parts.append(current_part)
                current_part = ""

            continue

        if c == "|" and not inside_squotes and not inside_dquotes and not is_escaped:
            # Handle the pipe
            if current_part:
                parts.append(current_part)
                current_part = ""
            pipeline.append(UserInput(parts, out_file, err_file))
            parts = []
            out_file = None
            err_file = None
            continue

        if c == "\\" and not inside_squotes and not is_escaped:
            continue

        if c == "'" and not inside_dquotes and not is_escaped:
            inside_squotes = not inside_squotes
            continue

        if c == '"' and not inside_squotes and not is_escaped:
            inside_dquotes = not inside_dquotes
            continue

        if c == " " and not (inside_squotes or inside_dquotes) and not is_escaped:
            if current_part:
                if is_reading_output_file:
                    # we were reading the output file, so the current part is actually the file name
                    out_file = (current_part, is_append)
                elif is_reading_error_file:
                    # we were reading the error file, so the current part is actually the file name
                    err_file = (current_part, is_append)
                else:
                    parts.append(current_part)

                is_append = False
                is_reading_error_file = False
                is_reading_output_file = False
                current_part = ""
            continue

        current_part += c

    if current_part:
        if is_reading_output_file:
            # we were reading the output file, so the current part is actually the file name
            out_file = (current_part, is_append)
        elif is_reading_error_file:
            # we were reading the error file, so the current part is actually the file name
            err_file = (current_part, is_append)
        else:
            parts.append(current_part)

    pipeline.append(UserInput(parts, out_file, err_file))
    return pipeline


def parse_input(input_line: str) -> Tuple[Command, List]:
    pipeline = split_command(input_line)

    commands: List[Tuple[Command, List]] = []
    for user_input in pipeline:
        command_name = user_input.input_parts[0]
        command_params = (
            user_input.input_parts[1:] if len(user_input.input_parts) > 1 else []
        )
        command = get_command(command_name)

        out_stream = None
        err_stream = None
        if user_input.output_file:
            mode = "a" if user_input.output_file[1] else "w"
            out_stream = open(user_input.output_file[0], mode)
        if user_input.error_file:
            mode = "a" if user_input.error_file[1] else "w"
            err_stream = open(user_input.error_file[0], mode)

        command.set_streams(out_stream=out_stream, err_stream=err_stream)
        commands.append((command, command_params))

    if len(commands) > 1:
        # Handle the pipe
        pipe_command = PipeCommand(commands)
        command = pipe_command
        command_params = []
    else:
        command, command_params = commands[0]

    return (command, command_params)


cached_available_items = set()


def handle_tab_completion(text: str, state: int) -> Optional[str]:
    global cached_available_items

    current_inut_line = readline.get_line_buffer()
    input_line_parts = current_inut_line.split(" ")

    is_argument_completion = len(input_line_parts) > 1

    if state == 0:
        builtin_commands = list(BUILTIN_COMMANDS_FACTORY.keys())
        local_files = os.listdir(os.getcwd())
        path_files = find_potential_files_in_path(text)
        cached_available_items = set(builtin_commands + local_files + path_files)
        # TODO handle argument completion

    suggestions = [item for item in cached_available_items if item.startswith(text)]

    # print(f"text: {text}, state: {state}, input_line_parts: {input_line_parts}, suggestions: {suggestions}")

    if len(suggestions) > state:
        # If there is only one suggestion, add a trailing space
        add_trailing_space = len(suggestions) == 1
        return suggestions[state] + (" " if add_trailing_space else "")

    return None


history_items_loaded_on_startup = 0


def main():
    readline.set_completer(handle_tab_completion)
    readline.parse_and_bind("tab: complete")

    hist_file = os.environ.get("HISTFILE")
    if hist_file and os.path.isfile(hist_file):
        global history_items_loaded_on_startup
        readline.read_history_file(hist_file)
        history_items_loaded_on_startup = readline.get_current_history_length()

    while True:
        user_input = input("$ ")

        if not user_input:
            continue

        command, params = parse_input(user_input)
        try:
            command.execute(params)
        except CommandError as e:
            print(f"{command.command_name}: {e}", file=sys.stderr)
        finally:
            command.close_streams()


if __name__ == "__main__":
    main()
