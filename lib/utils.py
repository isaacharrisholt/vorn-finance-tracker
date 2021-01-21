import os

colors_installed = True

try:
    from colorama import Fore, Style
except ModuleNotFoundError:
    colors_installed = False

if colors_installed:
    colors = {"RED": Fore.LIGHTRED_EX, "GREEN": Fore.GREEN, "BLUE": Fore.LIGHTBLUE_EX, "RESET": Fore.RESET}
else:
    colors = {"RED": "", "GREEN": "", "BLUE": "", "RESET": ""}


def cls():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def pprint(string):
    formatted_string = string.format(**colors)
    print(formatted_string)


def pinput(string):
    formatted_string = string.format(**colors)
    return input(formatted_string)
