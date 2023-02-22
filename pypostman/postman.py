import glob
from typing import List

from .modules.logger import Log
from .environment import Environment
from .collection import Collection
from .request import Request

log = Log()


class Postman:
    def __init__(self) -> None:
        pass

    def get_postman_environment_files(self, dir: str) -> List[str]:
        """
        This function returns a list of all the postman environments in the given directory -
        if the file name contains .postman_environment.json
        """
        environments = glob.glob(f"{dir}/*")
        environments = [
            environment
            for environment in environments
            if ".postman_environment.json" in environment
        ]
        return environments

    def get_postman_collection_files(self, dir: str) -> List[str]:
        """
        This function returns a list of all the postman collections in the given directory -
        if the file name contains .postman_collection.json
        """
        collections = glob.glob(f"{dir}/*")
        collections = [
            collection
            for collection in collections
            if ".postman_collection.json" in collection
        ]
        return collections

    def _get_environments(self, dir: str) -> List[Environment]:
        """
        Retrieve a list of Postman environments from the given directory.

        Args:
            dir (str): The directory containing Postman environments.

        Returns:
            List[Environment]: List of Postman environments.
        """
        environment_files = self.get_postman_environment_files(dir=dir)
        return [
            Environment.load(environment_file=environment_file)
            for environment_file in environment_files
        ]

    def _get_environment(
        self, environments: List[Environment], name: str
    ) -> Environment:

        """
        This function finds an Environment in a list of Environments based on its name and returns it.

        Args:
            environments (List[Environment]): List of Environment objects.
            name (str): Name of the Environment to be found.

        Returns:
            Environment: Environment object with the same name as the argument.
        """
        for environment in environments:
            if environment.name == name:
                return environment

    def _get_collections(self, dir: str) -> List[Collection]:
        """
        Gets the postman collection files in the given directory and returns a list of Collection objects.
        If no collection files are found, an error is logged.

        Parameters:
            dir (str): The directory path to search for postman collection files

        Returns:
            List[Collection]: A list of Collection objects
        """
        collections_files = self.get_postman_collection_files(dir=dir)
        if len(collections_files) > 0:
            return [
                Collection(collection_file=collection_file)
                for collection_file in collections_files
            ]
        log.error(f'No collection files were found in path "{dir}"')

    def _get_collection(self, name: str, collections: List[Collection]) -> Collection:
        """
        Gets the specified collection from the list of collections.

        Args:
            name (str): Name of the collection.
            collections (List[Collection]): List of collections.

        Returns:
            Collection: The specified collection.

        Raises:
            error (Exception): No collection named "{name}" was found.
        """
        for collection in collections:
            if collection._info.name == name:
                return collection

        log.error(f'No collection named "{name}" was found.')

    def _get_requests(self, collection: Collection) -> List[Request]:
        """
        This function returns a list of requests from a given collection.

        Args:
            collection (Collection): The collection to get requests from.

        Returns:
            List[Request]: A list of requests from the collection.
        """
        requests = collection._requests
        return requests

    def _get_request(self, name: str, requests: List[Request]):
        """
        Get the request object from the list of requests.

        Args:
            name (str): The name of the request.
            requests (List[Request]): The list of requests.

        Returns:
            Request: The request object.
        """
        for request in requests:
            if request.name == name:
                return request

        log.error(f"The request {name} was not found. Please verify the request name.")
