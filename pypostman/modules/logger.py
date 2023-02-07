import sys
from requests import Response
from logbook import Logger, StreamHandler

# from loguru import logger


class Log(Logger):
    def __init__(self) -> None:
        """
        Sets loging and inherits from Logger
        """

        super().__init__("Message")
        # Used to get messages from retry. No messages if removed.
        # logging.basicConfig(level=logging.DEBUG) # USE THIS TO DEBG THE PACKAGE
        # Logbook logger.
        StreamHandler(sys.stdout).push_application()

    def request(self, url: str, message: str = "->") -> None:
        """
        Logs the request
        """
        self.info(f"{message} Requesting data from: {url}")

    def raise_error(self, url: str, response: Response) -> None:
        """
        Logs the api url response error text, status code -
        headers and raises for status.
        """
        self.error(f"{url} response text: {response.text}")
        self.error(f"{url} response code: {response.status_code}")
        self.error(f"{url} response headers: {response.headers}")
        response.raise_for_status()

    def errors(self, url: str, response: Response) -> None:
        """
        Logs the api url response error text, status code -
        headers and raises for status.
        """
        self.error(f"{url} response text: {response.text}")
        self.error(f"{url} response code: {response.status_code}")
        self.error(f"{url} response headers: {response.headers}")

    def successful(self, url: str, message: str = "->") -> None:
        """
        Logs the successful api requests.
        """
        self.info(f"{message} Response sucessful from: {url}")
