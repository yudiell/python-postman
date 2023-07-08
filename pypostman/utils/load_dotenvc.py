import os
import argparse
import pyAesCrypt
from getpass import getpass
from dotenv import load_dotenv

from pypostman.modules.logger import Log

log = Log()


def encrypt_file() -> str:
    # Create a parser
    parser = argparse.ArgumentParser(description="Encrypt a file")

    # Add the arguments
    parser.add_argument(
        "-p",
        "--password",
        type=str,
        required=True,
        help="The password to encrypt the file",
    )
    parser.add_argument(
        "-f", "--file", type=str, required=True, help="The path to the file to encrypt"
    )

    # Parse the arguments
    args = parser.parse_args()

    # File to be encrypted
    filepath = args.file
    password = args.password

    # encryption/decryption buffer size - 64K
    bufferSize = 64 * 1024

    # Confirm password
    confirm_password = getpass("Please confirm your password: ")

    if password != confirm_password:
        raise ValueError("Passwords do not match!")

    # generate encrypted file path
    encrypted_filepath = filepath + ".aes"

    # encrypt the file
    pyAesCrypt.encryptFile(filepath, encrypted_filepath, password, bufferSize)

    # Create a parser
    parser = argparse.ArgumentParser(description="Encrypt a file")

    try:
        log.info("Encrypted file:", encrypted_filepath)
    except ValueError as ve:
        log.error(ve)


def decrypt_and_loadenv(
    password: str, filepath: str, remove_decrypted: bool = True
) -> dict:
    """
    Decrypts an AES encrypted file and loads its contents to the dotenv.

    Parameters:
    password (str): The password to decrypt the AES encrypted file.
    filepath (str): The path to the AES encrypted file that needs to be decrypted.
    remove_decrypted (bool): A flag that, if True, removes the decrypted file after its contents are loaded to the dotenv.
                             Default value is True. If False, the decrypted file will remain in the file system,
                             and its path will be logged.

    Returns:
    dict: A dictionary containing the loaded dotenv variables. The dictionary keys are the variable names and
          the values are the variable values.

    Note:
    The function doesn't explicitly return a dictionary. The loaded dotenv variables can be accessed using
    os.getenv() or os.environ in the rest of your code.
    """
    # Encryption/decryption buffer size - 64K
    bufferSize = 64 * 1024

    # Decrypted file path (temporary)
    decrypted_filepath = filepath.replace(".aes", "")

    # Decrypt the file
    pyAesCrypt.decryptFile(filepath, decrypted_filepath, password, bufferSize)

    # Load the decrypted content to dotenv
    load_dotenv(dotenv_path=decrypted_filepath)
    # Delete the temporary decrypted file
    if remove_decrypted:
        os.remove(decrypted_filepath)
    else:
        log.info(decrypted_filepath)


if __name__ == "__main__":
    encrypt_file()
