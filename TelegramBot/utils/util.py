import logging
from random import choice
from typing import Dict
from os.path import exists, isfile


def is_file_valid(path: str):
    """
    Check if the given path is a valid file.

    Args:
        path (str): The path to check.

    Returns:
        bool: True if the path exists, is a file, and is not empty. False otherwise.
    """
    if not exists(path) or not isfile(path) or not path:
        return False
    return True


def is_path_accessible(path):
    """
    Check if the given path is accessible for reading.

    Args:
        path (str): The path to check.

    Returns:
        bool: True if the path is accessible, False otherwise.
    """
    if not path:
        return False

    try:
        with open(path) as _:
            pass
        return True
    except IOError as _:
        return False


def check_path(path: str) -> None:
    """
    Check if the given path is valid and accessible. Raises an exception if any check fails.

    Args:
        path (str): The path to check.

    Raises:
        ValueError: If the path is not a valid file.
        IOError: If the path is not accessible for reading.
    """
    if not is_file_valid(path):
        raise ValueError(f"The path '{path}' is not a valid file.")
    if not is_path_accessible(path):
        raise IOError(f"The path '{path}' is not accessible.")


def save_phrases_to_file(filename: str, phrases: Dict[int, str]) -> None:
    """
    Save phrases to a file.

    Args:
        filename (str): The name of the file to save the phrases to.
        phrases (Dict[int, str]): A dictionary of phrases where keys are integers and values are strings.
    """
    try:
        with open(filename, "w", encoding="utf-8") as file:
            for phrase in phrases.values():
                file.write(f"{phrase}\n")
        logging.info(f"Successfully saved phrases to {filename}.")
    except Exception as e:
        logging.error(f"Error saving phrases to file {filename}: {e}")


def load_phrases_from_file(filename: str) -> Dict[int, str]:
    """
    Load phrases from a file.

    Args:
        filename (str): The name of the file to load the phrases from.

    Returns:
        Dict[int, str]: A dictionary of phrases where keys are integers and values are strings.
    """
    phrases = {}
    check_path(filename)

    try:
        with open(filename, "r", encoding="utf-8") as file:
            for idx, line in enumerate(file, start=1):
                phrases[idx] = line.strip()
        logging.info(f"Successfully loaded phrases from {filename}.")
    except FileNotFoundError:
        logging.error(f"File {filename} not found.")
    except Exception as e:
        logging.error(f"Error loading phrases from file {filename}: {e}")
    return phrases


def get_random_phrase(phrases: Dict[int, str]) -> str:
    """
    Get a random phrase from the given dictionary of phrases.

    Args:
        phrases (Dict[int, str]): Dictionary of phrases where keys are integers and values are strings.

    Returns:
        str: A random phrase as a string.
    """
    try:
        return choice(list(phrases.values()))
    except IndexError:
        logging.error("The phrases dictionary is empty.")
        return "No phrases available."
    except Exception as e:
        logging.error(f"Error getting random phrase: {e}")
        return "An error occurred while getting a random phrase."
