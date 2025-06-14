import sys
import os

commands = {}
space = " "
errors = []
path = os.environ["PATH"]


def stopShell(args=["0"]):
    sys.exit(int(args[0]))


def echo(args):
    print(space.join(args))


def typeOf(args=["invalid"]):
    checkType = space.join(args)
    if checkType in commands:
        print(f"{checkType} is a shell builtin")
    elif findExe(args[0]):
        exePath = findExe(args[0])
        print(f"{args[0]} is {exePath}")
    else:
        print(f"{checkType}: not found")


def findExe(exe):
    paths = path.split(":")

    for pathDir in paths:
        try:
            for filename in os.listdir(pathDir):
                if filename == exe:
                    filePath = os.path.join(pathDir, filename)
                    if os.path.isfile(filePath) and os.access(filePath, os.X_OK):
                        return filePath
        except:
            errors.append("bad path permissions")

    return None


def handleInput(inputs):
    global commands
    commands.update({"exit": stopShell, "echo": echo, "type": typeOf})
    inputArr = inputs.split(" ")

    if inputArr[0] in commands:
        commands[inputArr[0]](inputArr[1:] if len(inputArr) > 1 else ["0"])
    elif findExe(inputArr[0]):
        os.system(inputs)
    else:
        print(f"{inputs}: command not found")

    main()


def main():
    # Uncomment this block to pass the first stage
    sys.stdout.write("$ ")

    # Wait for user input
    command = input()
    handleInput(command)


if __name__ == "__main__":
    main()