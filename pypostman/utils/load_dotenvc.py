import os
import argparse
import pyAesCrypt
from getpass import getpass
from dotenv import load_dotenv


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
        print("Encrypted file:", encrypted_filepath)
    except ValueError as ve:
        print(ve)


def decrypt_and_load_env(
    password: str, filepath: str, remove_decrypted: bool = True
) -> dict:
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
        print(decrypted_filepath)
