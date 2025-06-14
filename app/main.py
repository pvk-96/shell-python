import os
import sys
from typing import List, Tuple


class Shell:
    def __init__(self):
        self.current_dir = os.getcwd()
        self.commands = {
            "exit": self.exit,
            "echo": self.echo,
            "type": self.type,
            "pwd": self.pwd,
            "cd": self.cd,
        }

    def exit(self, *args, **kwargs):
        status_code = args[0] if args else 0
        sys.exit()

    def echo(self, *args, **kwargs):
        if args:
            sys.stdout.write(" ".join(args))
        sys.stdout.write("\n")

    def type(self, *args, **kwargs):
        name = args[0]
        if name in self.commands:
            sys.stdout.write(f"{name} is a shell builtin")
        elif file_path := self._resolve_file_executability(name):
            sys.stdout.write(f"{name} is {file_path}")
        else:
            sys.stdout.write(f"{name}: not found")
        sys.stdout.write("\n")

    def pwd(self, *args, **kwargs):
        sys.stdout.write(self.current_dir + "\n")

    def cd(self, *args, **kwargs):
        path = args[0]
        if path == "~":
            self.current_dir = os.environ.get("HOME")
        elif os.path.isabs(path) and os.path.isdir(path):
            self.current_dir = path
        elif os.path.isdir(os.path.join(self.current_dir, path)):
            new_path = os.path.abspath(os.path.join(self.current_dir, path))
            if os.path.isdir(new_path):
                self.current_dir = new_path
            else:
                sys.stdout.write(f"cd: {path}: No such file or directory\n")
        else:
            sys.stdout.write(f"cd: {path}: No such file or directory\n")

    def _resolve_file_executability(
        self, cmd, mode=os.F_OK | os.X_OK, path=None
    ) -> str | None:
        use_bytes = isinstance(cmd, bytes)

        dirname, cmd = os.path.split(cmd)
        if dirname:
            path = [dirname]
        else:
            if path is None:
                path = os.environ.get("PATH", None)
                if path is None:
                    try:
                        path = os.confstr("CS_PATH")
                    except (AttributeError, ValueError):
                        path = os.defpath

            if not path:
                return None
            if use_bytes:
                path = os.fsencode(path)
                path = path.split(os.fsencode(os.pathsep))
            else:
                path = os.fsdecode(path)
                path = path.split(os.pathsep)

        files = [cmd]

        seen = set()
        for dir in path:
            normdir = os.path.normcase(dir)
            if not normdir in seen:
                seen.add(normdir)
                for thefile in files:
                    name = os.path.join(dir, thefile)
                    if (
                        os.path.exists(name)
                        and os.access(name, mode)
                        and not os.path.isdir(name)
                    ):
                        return name
        return None

    #  echo 'test     hello' 'example''world'
    #  Expected: "test     hello exampleworld"

    def _parse_echo_arguments(self, arguments):
        args = []
        in_quote = False
        quote_char = ""
        current = ""
        i = len("echo") + 1

        while i < len(arguments):
            c = arguments[i]
            if c in ("'", '"'):
                if not in_quote:
                    in_quote = True
                    quote_char = c
                elif quote_char == c:
                    in_quote = False
                    quote_char = ""
                else:
                    current += c
                i += 1
            elif c == "\\":
                i += 1
                if quote_char == '"':
                    if i < len(arguments) and arguments[i] in (
                        "\\",
                        '"',
                        "`",
                        "$",
                        "\n",
                    ):
                        current += arguments[i]
                    else:
                        current += c
                    i += 1
                elif quote_char == "'":
                    current += c
                elif i < len(arguments):
                    current += arguments[i]
                    i += 1
            elif in_quote:
                current += c
                i += 1
            else:
                if c == " " and current:
                    args.append(current)
                    current = ""
                elif c != " ":
                    # Handle non single/double quotes
                    current += c
                i += 1
        if current:
            args.append(current)
        return args

    def _input_spliter(self, cmd: str) -> Tuple[str, List[str]]:
        splited_cmd = cmd.split()
        if splited_cmd[0].strip() == "echo":
            return splited_cmd[0].strip(), self._parse_echo_arguments(cmd)
        return splited_cmd[0].strip(), splited_cmd[1:]

    def input_dispachter(self, cmd: str):
        cmd_name, cmd_args = self._input_spliter(cmd)
        if cmd_name in self.commands:
            self.commands[cmd_name](*cmd_args)
            return
        elif self._resolve_file_executability(cmd_name):
            os.system(cmd)
            return
        else:
            sys.stdout.write(f"{cmd_name}: command not found\n")

    def run(self):
        while True:
            sys.stdout.write("$ ")
            cmd = input()
            self.input_dispachter(cmd)


if __name__ == "__main__":
    shell = Shell()
    shell.run()