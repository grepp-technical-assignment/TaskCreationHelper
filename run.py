# Standard libraries
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
    from AzadLibrary import AzadCore
    import AzadLibrary.constants as Const
    from AzadLibrary.misc import barLine

    subcommand = argv[1] if len(argv) > 1 else "help"
    print(barLine("Azad Library"))
    atexit.register(print, barLine("Azad Library Termination"))
    logging.captureWarnings(True)

    if subcommand == "help":  # Help
        with open(Const.ResourcesPath / "etc/help.txt", "r") as helpFile:
            print(helpFile.read())

    elif subcommand == "init":  # Interactive initialization

        startInformation = deepcopy(Const.StartingConfigState)
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

        # Write basic files
        with open(Path(folderName) / "config.json", "w") as configFile:
            json.dump(startInformation, configFile, indent=4)
        with open(Path(folderName) / "statement.md", "w") as statementFile:
            with open(Const.ResourcesPath / "etc/default_statement.md", "r") \
                    as defaultStatementFile:
                statementFile.write(defaultStatementFile.read())

    elif subcommand in ("full", "produce", "generate"):  # Actual run process

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

        # Run total pipeline
        Core = AzadCore(configFilePath)
        mode: Const.AzadLibraryMode = {
            "full": Const.AzadLibraryMode.Full,
            "produce": Const.AzadLibraryMode.Produce,
            "generate": Const.AzadLibraryMode.GenerateCode,
        }[subcommand]
        Core.run(mode)

    else:
        raise ValueError(
            "Given subcommand %s is not valid. Please try \"python3 run.py help\"." %
            (subcommand,))
