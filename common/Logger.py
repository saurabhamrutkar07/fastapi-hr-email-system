import enum
import logging

# Common log messages used throughout the application.
LOGGER_INFO_START_TEXT = "Started execution of function : "
LOGGER_INFO_END_TEXT = "Completed execution of function : "
LOGGER_INFO_QUERY_START_TEXT = "Executing query on table : "
LOGGER_INFO_QUERY_END_TEXT = "Completed query execution"
LOGGER_INFO_CACHE_QUERY_START_TEXT = "Executing query on cache with key:"
LOGGER_INFO_CACHE_QUERY_END_TEXT = "Completed cache query execution"


class logLevel(enum.Enum):
    """
    Enum to store all supported logging levels.
    Instead of writing logging.INFO everywhere,
    we can write logLevel.INFO.
    """

    NOTSET = logging.NOTSET
    INFO = logging.INFO
    ERROR = logging.ERROR
    DEBUG = logging.DEBUG
    WARNING = logging.WARNING
    CRITICAL = logging.CRITICAL


class Logger:

    # Class variable.
    # Shared by every call to Logger.get_logger().
    # Initially no logger exists.
    _logger = None

    @classmethod
    def get_logger(cls):
        """
        Creates the logger only once and returns the same logger
        every time this method is called.

        This follows the Singleton pattern.
        """

        # Check whether the logger has already been created.
        if cls._logger is None:

            # Create a logger named "ApplicationLogger".
            # If a logger with this name already exists,
            # logging.getLogger() returns the same logger.
            cls._logger = logging.getLogger("ApplicationLogger")

            # Set the minimum logging level.
            # INFO means INFO, WARNING, ERROR and CRITICAL
            # will be shown.
            # DEBUG logs will be ignored.
            cls._logger.setLevel(logLevel.INFO.value)

            # Define how every log message should appear.
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)s | %(message)s"
            )

            # Create a handler.
            # StreamHandler() prints logs to the console/terminal.
            console_handler = logging.StreamHandler()

            # Apply the formatter to the console handler.
            console_handler.setFormatter(formatter)

            # Attach the console handler to the logger.
            # Without a handler, the logger doesn't know
            # where to write the logs.
            cls._logger.addHandler(console_handler)

        # Return the same logger object every time.
        return cls._logger

    @classmethod
    def info(cls, message):
        """
        Logs an INFO level message.
        """
        cls.get_logger().info(message)

    @classmethod
    def debug(cls, message):
        """
        Logs a DEBUG level message.
        """
        cls.get_logger().debug(message)

    @classmethod
    def error(cls, message):
        """
        Logs an ERROR level message.
        """
        cls.get_logger().error(message)

    @classmethod
    def warning(cls, message):
        """
        Logs a WARNING level message.
        """
        cls.get_logger().warning(message)

    @classmethod
    def critical(cls, message):
        """
        Logs a CRITICAL level message.
        """
        cls.get_logger().critical(message)