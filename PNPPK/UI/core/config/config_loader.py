import yaml
import yaml.scanner


class ConfigLoaderException(Exception):
    """
    Base exception for ConfigLoader.

    This exception serves as the parent class for all configuration file-related errors.
    It provides a unified exception hierarchy for issues encountered during configuration
    file loading and parsing.
    """


class ConfigFileNotFoundError(ConfigLoaderException):
    """
    Raised when the configuration file is not found.

    This exception is raised if the specified configuration file does not exist
    at the provided file path.

    Attributes:
        file_path: str
            The path to the configuration file that was not found.
    """

    def __init__(self, file_path: str):
        """
        Initializes the ConfigFileNotFoundError with the missing file path.

        :param file_path: str
            The path to the configuration file that could not be found.

        Algorithm:
        1. Store the file path as an attribute.
        2. Pass an appropriate error message to the base Exception class.

        Edge Cases:
        - Invalid or non-string file_path raises a TypeError
          (inside Exception.__init__()).
        """
        super().__init__(f"Configuration file not found: {file_path}")
        self.file_path = file_path


class ConfigFileFormatError(ConfigLoaderException):
    """
    Raised when the configuration file has invalid YAML format.

    This exception is raised if the configuration file exists but contains syntax
    errors or invalid YAML formatting.

    Attributes:
        file_path: str
            The path to the configuration file.
        error: Exception
            The original exception raised by the YAML parser.
    """

    def __init__(self, file_path: str, error: Exception):
        """
        Initializes the ConfigFileFormatError with file path and parsing error.

        :param file_path: str
            The path to the configuration file.
        :param error: Exception
            The exception raised during YAML parsing.

        Algorithm:
        1. Store the file path and original error as attributes.
        2. Pass an appropriate error message to the base Exception class.

        Edge Cases:
        - Invalid error type raises TypeError during initialization
          (inside Exception.__init__()).
        """
        super().__init__(f"Invalid YAML format in file {file_path}: {error}")
        self.file_path = file_path
        self.error = error


class ConfigLoader:
    """
    A utility class to load and parse YAML configuration files.

    This class provides a static method to load YAML files and ensures
    proper error handling for missing files and invalid formats.
    """

    @staticmethod
    def load_config(file_path: str) -> dict:
        """
        Loads a YAML configuration file.

        :param file_path: str
            Path to the YAML file.
        :return: dict
            The configuration data as a dictionary.
        :raises ConfigFileNotFoundError: If the file does not exist.
        :raises ConfigFileFormatError: If the YAML format is invalid.
        :raises ConfigLoaderException: For unexpected errors during file loading.

        Algorithm:
        1. Attempt to open the specified file.
        2. Parse the file using yaml.safe_load().
        3. Return the parsed configuration as a dictionary.

        Edge Cases:
        - Missing file raises ConfigFileNotFoundError
          (inside: Algorithm p. 1).
        - Invalid YAML syntax raises ConfigFileFormatError
          (inside: Algorithm p. 2).
        - Any unexpected exceptions are raised as ConfigLoaderException
          (inside: Algorithm p. 3).
        """
        try:
            with open(file_path, "r") as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            raise ConfigFileNotFoundError(file_path)
        except (yaml.YAMLError, yaml.scanner.ScannerError) as e:
            raise ConfigFileFormatError(file_path, e)
        except Exception as e:
            raise ConfigLoaderException(
                f"Unexpected error loading configuration file {file_path}: {e}"
            )
