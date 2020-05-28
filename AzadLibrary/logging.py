"""
This module is used to manage log.
"""

# Standard libraries
import atexit
from datetime import datetime, timedelta
import warnings
from pathlib import Path

# Azad library
from .constants import LogLevel


class Logger:
    """
    Logger object. It logs Azad library behaviour.
    """

    # Constants
    DefaultFlushingDelay = timedelta(seconds=5)
    DefaultStrfMessage = "%Y/%m/%d %H:%M:%S.%f (%Z)"

    def __init__(self, mainLogFile: str, activated: bool = True):
        # Log activation
        self.activated = activated
        if not self.activated:
            return

        # Find log file and open(or make) it
        logFilePath = Path(mainLogFile)
        if logFilePath.exists():
            if logFilePath.is_file():
                self.mainLogFile = open(mainLogFile, "a")
            else:
                raise FileNotFoundError("Given log file is not a file")
        else:
            self.mainLogFile = open(mainLogFile, "w")

        # Init message
        bar = "=" * 120
        initMessage = "%s\n Azad Library %s\n%s\n" % (bar, self.datestr(), bar)
        self.mainLogFile.write(initMessage)

        # Internal settings
        self.flush()
        atexit.register(self.terminate)

    def flush(self):
        self.mainLogFile.flush()
        self.lastFlushed = datetime.now()

    def terminate(self):
        """
        Terminate current logger.
        """
        self.mainLogFile.close()

    @staticmethod
    def datestr(timestamp: datetime = None, syntax: str = None):
        result = (timestamp if timestamp else datetime.now()) \
            .strftime(syntax if syntax else Logger.DefaultStrfMessage)
        if result.endswith(" ()"):
            result = result.replace(" ()", "")
        return result

    @staticmethod
    def prepareMessage(message: str, priority: LogLevel = LogLevel.Info,
                       timestamp: datetime = None) -> str:
        return "[%s] %7s %s" % (Logger.datestr(timestamp),
                                "[%s]" % (priority.value,), message)

    def log(self, message: str, priority: LogLevel = LogLevel.Info,
            warnCategory=Warning, maxlen: int = 120, maxstdoutlen: int = 120):
        """
        Log given message with priority.
        """
        # If logger is not activated then return
        if not self.activated:
            return

        # Validate log-ability
        if maxlen < 4:
            raise ValueError("Invalid maxlen %d" % (maxlen,))
        elif self.mainLogFile.closed:
            warnings.warn(
                "Tried logging when main logfile is already closed. This log is dismissed.")
            return

        # Make message
        timestamp = datetime.now()
        logMessage = self.prepareMessage(message, priority, timestamp)
        if len(logMessage) > maxlen:
            logMessage = logMessage[:maxlen - 4] + " ..."
        self.mainLogFile.write(logMessage + "\n")

        # Flush if flushable condition
        if timestamp - self.lastFlushed > Logger.DefaultFlushingDelay or \
                priority is LogLevel.Error:
            self.flush()

        # Make stdout message if priority is high enough
        if priority in (LogLevel.Error, LogLevel.Warn, LogLevel.Info):
            stdoutMsg = logMessage if len(
                logMessage) <= maxstdoutlen else (logMessage[:(maxstdoutlen - 4)] + " ...")
            if priority is LogLevel.Warn:
                warnings.warn(stdoutMsg, warnCategory)
            print(stdoutMsg)

    # Short alias of log method
    def error(self, message: str, maxlen: int = 250):
        self.log(message, LogLevel.Error, maxlen=maxlen)

    def warn(self, message: str, warnCategory=Warning, maxlen: int = 250):
        self.log(message,
                 LogLevel.Warn,
                 warnCategory=warnCategory,
                 maxlen=maxlen)

    def info(self, message: str, maxlen: int = 250):
        if maxlen >= 0 and len(message) > maxlen:
            message = message[:maxlen]
        self.log(message, LogLevel.Info, maxlen=maxlen)

    def debug(self, message: str, maxlen: int = 1200):
        self.log(message, LogLevel.Debug, maxlen=maxlen)
