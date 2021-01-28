import os

colors_installed = True

try:
    from colorama import Fore, Style
except ModuleNotFoundError:
    colors_installed = False

if colors_installed:
    colors = {"RED": Fore.LIGHTRED_EX, "GREEN": Fore.GREEN, "YELLOW": Fore.LIGHTYELLOW_EX, "RESET": Fore.RESET}
else:
    colors = {"RED": "", "GREEN": "", "YELLOW": "", "RESET": ""}

LINE = "------------------------------------------------------------------------------------------------------------" \
       "-------"


def cls():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def pprint(string):
    formatted_string = string.format(**colors)
    print(f"\n{LINE}")
    print(formatted_string)
    print(f"{LINE}\n")


def pinput(string):
    formatted_string = string.format(**colors)
    print(f"\n{LINE}")
    print(formatted_string)
    return input(f"{LINE}\n: ")
