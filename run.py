# Standard libraries
from copy import deepcopy
import json
import re
import os
import sys
from pathlib import Path
import warnings
import logging
import atexit
import argparse
import traceback


def checkConfigFile(parsedResult: argparse.Namespace) -> Path:
    """
    Check configuration file and return its path.
    """

    # Check config.json file
    configFilePath = Path(
        parsedResult.config if parsedResult.config else os.getcwd())
    if not configFilePath.exists():
        raise FileNotFoundError(
            "Given path %s not found" %
            (configFilePath,))
    elif configFilePath.is_file():
        if not configFilePath.name.endswith("config.json"):
            warnings.warn("Given file name is not config.json")
    else:  # Given path is directory
        configFilePath = configFilePath / "config.json"
        if not configFilePath.exists():
            raise FileNotFoundError("%s not found" % (configFilePath,))
    return configFilePath


# Main Execution
if __name__ == "__main__":

    # Check Python version first
    import AzadLibrary.constants as Const
    currentPythonVersion = (
        sys.version_info.major, sys.version_info.minor, sys.version_info.micro)
    if currentPythonVersion < Const.MinimumPythonVersion:
        currentPythonVersionStr = ".".join(
            str(c) for c in currentPythonVersion)
        minimumPythonVersionStr = ".".join(
            str(c) for c in Const.MinimumPythonVersion)
        raise Exception(
            "Failed to qualify Python version; Given %s < Minimum %s" %
            (currentPythonVersionStr, minimumPythonVersionStr))

    # Create argument parser and parse it
    argParser = argparse.ArgumentParser(prog="TaskCreationHelper")
    argParser.add_argument(
        "-i", "--init", help="Initialize Problem Repository", action="store_true")
    argParser.add_argument(
        "-l", "--level",
        help="Specify the level of TCH execution (generate - produce - stress - full)",
        default="full")
    argParser.add_argument(
        "-s", "--stress_index", help="Specify the index of stress", type=int, default=None)
    argParser.add_argument(
        "-c", "--config", help="Give the path to the config.json or folder")
    argParser.add_argument(
        "-v", "--version", help="Show the version of TCH", action="version",
        version="TaskCreationHelper v%s" % (Const.AzadLibraryVersion,))
    argParser.add_argument(
        "-p", "--pause_on_err", help="Pause on error", action="store_true")
    argParser.add_argument(
        "-r", "--reduced_debug", help="Reduce amount of debugging", action="store_true")
    parsedResult = argParser.parse_args(sys.argv[1:])

    # Bar line
    from AzadLibrary import AzadCore
    from AzadLibrary.misc import barLine, pause
    print(barLine("Azad Library"))
    atexit.register(print, barLine("Azad Library Termination"))
    logging.captureWarnings(True)

    # Interactive initialization
    if parsedResult.init:

        # Create basic information
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

    # Actual run process
    elif parsedResult.level in ("full", "produce", "generate", "stress"):

        # Get configuration file path
        configFilePath = checkConfigFile(parsedResult)

        # Run total pipeline
        Core = AzadCore(
            configFilePath,
            logLevel=logging.INFO if parsedResult.reduced_debug else logging.NOTSET)
        mode: Const.AzadLibraryMode = {
            "full": Const.AzadLibraryMode.Full,
            "produce": Const.AzadLibraryMode.Produce,
            "generate": Const.AzadLibraryMode.GenerateCode,
            "stress": Const.AzadLibraryMode.StressTest,
        }[parsedResult.level]
        logger = logging.getLogger(__name__)

        if mode is Const.AzadLibraryMode.StressTest and parsedResult.stress_index is None:
            while True:
                print("Enter stress test index:", end=' ')
                parsedResult.stress_index = input()
                if parsedResult.stress_index.isdigit():
                    parsedResult.stress_index = int(parsedResult.stress_index)
                    break
                else:
                    print("Please enter valid index.")

        try:
            Core.run(mode, stressTestIndex=parsedResult.stress_index)
        except BaseException as err:
            if parsedResult.pause_on_err:
                pause()
            logger.error("\n" + "".join(traceback.format_exception(
                type(err), err, err.__traceback__)))
            logger.error("TCH FAILED. Please look at log.")
            exit(1)
        else:
            logger.info("TCH SUCCEEDED!")

    else:
        raise ValueError(
            "Given subcommand %s is not valid." % (parsedResult.level,))
