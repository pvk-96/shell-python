import sys
import os
import shutil
import subprocess
import shlex


class Shell:
    def __init__(self):
        self.env_vars = os.environ.copy()
        self.current_dir = os.getcwd()
        self.commands = {
            "exit": self.handle_exit,
            "echo": self.handle_echo,
            "type": self.handle_type,
            "pwd": self.handle_pwd,
            "cd": self.handle_cd,
        }

    def handle_pwd(self, *args, **kwargs):
        sys.stdout.write(self.current_dir + "\n")

    def handle_cd(self, *args, **kwargs):
        """
        Args is not split, so we need to check if args[0] is a directory.
        For relative paths need to split the path and e.g. traverse up the tree.
        """
        # check if args 0 is a directory
        if len(args) == 0:
            sys.stdout.write("cd: missing argument\n")
            return
        # handle abs path
        if os.path.isabs(args[0]) and os.path.isdir(args[0]):
            self.current_dir = args[0]
        # Check if args 0 is a relative path, e.g. handle cd .. and cd ./dir
        elif os.path.isdir(os.path.join(self.current_dir, args[0])):
            # Resolve the path properly. even complex ones, e.g. ../dir/../dir2
            # use built in os.path.abspath to resolve the path, the complex part can be in the middle so we cant use startswith
            new_path = os.path.abspath(os.path.join(self.current_dir, args[0]))
            self.current_dir = new_path
        elif args[0] == "~":
            # Use from env vars
            self.current_dir = self.env_vars["HOME"]
        else:
            sys.stdout.write(f"cd: {args[0]}: No such file or directory\n")

    def handle_exit(self, *args, **kwargs):
        # if args is not none, use first arg as exit code
        exit_code = 0
        if args:
            try:
                exit_code = int(args[0])
            except ValueError:
                pass

        sys.exit(exit_code)

    def handle_echo(self, *args, **kwargs):
        # if args is not none, use first arg as exit code
        if args:
            sys.stdout.write(" ".join(args) + "\n")
        else:
            sys.stdout.write("\n")

    def _resolve_first_exec(self, name):
        # start by checking if the name is a shell builtin
        if name in self.commands:
            return name, "builtin"

        # to find the executable in the PATH
        file_path = shutil.which(name)
        if file_path:
            # check if the file is executable
            if os.access(file_path, os.X_OK):
                return file_path, "executable"
            else:
                return None, "not_executable"

        return None, None

    def handle_type(self, *args, **kwargs):
        if args:
            name = args[0]
            if name in self.commands:
                sys.stdout.write(f"{name} is a shell builtin\n")
                return
            file_path, exec_type = self._resolve_first_exec(name)
            if file_path:
                sys.stdout.write(f"{name} is {file_path}\n")
            else:
                sys.stdout.write(f"{name}: not found\n")

    def tokenize(self, command):
        # tokenize the command
        # this is a simple implementation, we can use shlex to handle single quotes
        tokens = []
        current_token = ""
        in_quotes = False
        for char in command:
            # If we see a quote, we need to toggle the in_quotes flag
            if char == "'":
                in_quotes = not in_quotes
                continue

            if char == " " and not in_quotes:
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
                continue

            current_token += char

        if current_token:
            tokens.append(current_token)
        return tokens

    def handle_command(self, command):
        split_command = shlex.split(command, posix=True)
        # print(split_command)
        if len(split_command) == 0:
            return
        command_name = split_command[0]
        name, _type = self._resolve_first_exec(command_name)
        # check if builtin, if so, run it
        args = split_command[1:]
        if name and _type == "builtin":
            self.commands[name](*args)
            return
        if name and _type == "executable":
            # For exec it needs to keep the quotes
            # we need to use subprocess to handle the exec
            try:
                result = subprocess.run(
                    [command_name] + args, cwd=self.current_dir, env=self.env_vars
                )
            except Exception as e:
                sys.stdout.write(f"{command_name}: {e}\n")
            return
        sys.stdout.write(f"{command_name}: command not found\n")

    def run(self):
        while True:
            if sys.stdin.isatty():
                # if stdin is a tty, we can use the prompt
                sys.stdout.write("$ ")
            command = input()
            self.handle_command(command)


if __name__ == "__main__":
    shell = Shell()
    shell.run()