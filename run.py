# Standard libraries
import typing
from copy import deepcopy
import json
import re
import os
from sys import argv
from pathlib import Path
import warnings
import logging
import atexit

# Main Execution
if __name__ == "__main__":

    # Azad library
    from AzadLibrary import AzadCore, StartingConfigState
    from AzadLibrary.misc import barLine

    subcommand = argv[1] if len(argv) > 1 else "help"
    print(barLine("Azad Library"))
    atexit.register(print, barLine("Azad Library Termination"))
    startInformation = deepcopy(StartingConfigState)
    logging.captureWarnings(True)

    if subcommand == "help":  # Help
        helpStr = """
<Documentation>
Usage: python3 run.py (subcommand) [args...]
List of subcommands:
    - help: "python3 run.py help"
        Print documentation.
    - full: "python3 run.py full [running_path / config_file_path]"
        Run full process - I/O data generation, source file validation, etc.
        You need a config.json file in running path.
    - produce_io: "python3 run.py produce_io [running_path / config_file_path]"
        Minimize validation process and produce I/O data file only.
        You need a config.json file in running path.
"""
        print(helpStr)

    elif subcommand == "init":  # Interactive initialization
        print("Let's initialize new problem folder.")
        print("Current location is \"%s\"." % (os.getcwd(),))
        folderNamePattern = re.compile("[A-Za-z0-9_]+(/[A-Za-z0-9_]+)*")
        while True:
            folderName = input("Enter problem's folder name: ").strip()
            if not folderName:
                print("Ok, exiting...")
                exit()
            elif not re.fullmatch(folderNamePattern, folderName):
                print("Wrong pattern for folder name given. Please try again.")
            elif Path(folderName).exists():
                print("Already existing folder. Please try again.")
            else:
                break
        author = input("Enter author(optional): ").strip()
        startInformation["author"] = author if author else "Unknown"
        problemName = input("Enter problem name(optional): ").strip()
        startInformation["name"] = problemName if problemName else "Untitled"
        os.makedirs(folderName)
        with open(Path(folderName) / "config.json", "w") as configFile:
            json.dump(startInformation, configFile, indent=4)

    elif subcommand in ("full", "produce_io"):  # Actual run process

        # Check config.json file
        configFilePath = Path(argv[2] if len(argv) > 2 else os.getcwd())
        if not configFilePath.exists():
            raise FileNotFoundError(
                "Given path %s not found" %
                (configFilePath,))
        elif configFilePath.is_file():
            if not configFilePath.name.endswith("config.json"):
                warnings.warn("Given file name is not config.json")
        else:  # path is directory
            configFilePath = configFilePath / "config.json"
            if not configFilePath.exists():
                raise FileNotFoundError("%s not found" % (configFilePath,))

        Core = AzadCore(configFilePath)
        if subcommand == "full":
            Core.checkAllSolutionFiles()
            Core.makeInputFiles()
            Core.makeOutputFiles()
        elif subcommand == "produce":
            Core.makeInputFiles()
            Core.makeOutputFiles()
        else:
            raise NotImplementedError

    else:
        raise ValueError(
            "Given subcommand %s is not valid. Please try \"python3 run.py help\"." %
            (subcommand,))
