import sys


def main():
    while True:
        sys.stdout.write("$ ")
        command = input()
        if command == "exit 0":
            break
        print(f"{command}: command not found")


if __name__ == "__main__":
    main()
