"""
This script provides functionalities for encrypting a file and decrypting an AES encrypted file.
The decrypted file's contents are then loaded into the environment using the dotenv library.
"""

import os
import argparse
import pyAesCrypt
from getpass import getpass
from dotenv import load_dotenv

from pypostman.modules.logger import Log

log = Log()  # Initialize the logger


def parse_arguments(description, arguments):
    """
    Parses command line arguments.

    Parameters:
    description (str): Description of the command line program.
    arguments (list): A list of tuples, where each tuple is an argument in the format (short_option, long_option, description).

    Returns:
    argparse.Namespace: The parsed command line arguments.
    """
    parser = argparse.ArgumentParser(description=description)
    for argument in arguments:
        parser.add_argument(
            argument[0], argument[1], type=str, required=True, help=argument[2]
        )
    return parser.parse_args()


def encrypt_file():
    """
    Encrypts a file with AES encryption. The password and file path are provided as command line arguments.
    """
    args = parse_arguments(
        "Encrypt a file",
        [
            ("-p", "--password", "The password to encrypt the file"),
            ("-f", "--file", "The path to the file to encrypt"),
        ],
    )
    filepath = args.file
    password = args.password
    bufferSize = 64 * 1024  # Encryption/decryption buffer size
    confirm_password = getpass("Please confirm your password: ")

    if password != confirm_password:
        log.error("Passwords do not match!")
        return

    encrypted_filepath = filepath + ".aes"  # Generate encrypted file path
    pyAesCrypt.encryptFile(
        filepath, encrypted_filepath, password, bufferSize
    )  # Encrypt the file

    try:
        log.info(
            f"Encrypted file: {encrypted_filepath}"
        )  # Log the path of the encrypted file
    except ValueError as ve:
        log.error(ve)


def decrypt_and_loadenv(password: str, filepath: str, remove_decrypted: bool = True):
    """
    Decrypts an AES encrypted file and loads its contents to the environment using the dotenv library.

    Parameters:
    password (str): The password to decrypt the AES encrypted file.
    filepath (str): The path to the AES encrypted file that needs to be decrypted.
    remove_decrypted (bool): A flag that, if True, removes the decrypted file after its contents are loaded to the environment.
                             Default value is True. If False, the decrypted file will remain in the file system,
                             and its path will be logged.
    """
    bufferSize = 64 * 1024  # Encryption/decryption buffer size
    decrypted_filepath = filepath.replace(".aes", "")  # Generate decrypted file path

    try:
        pyAesCrypt.decryptFile(
            filepath, decrypted_filepath, password, bufferSize
        )  # Decrypt the file
        load_dotenv(
            dotenv_path=decrypted_filepath
        )  # Load the decrypted content to environment
    except Exception as e:
        log.error(f"An error occurred during decryption: {str(e)}")
        return

    if remove_decrypted:
        os.remove(decrypted_filepath)  # Remove the decrypted file
    else:
        log.info(decrypted_filepath)  # Log the path of the decrypted file


if __name__ == "__main__":
    encrypt_file()
