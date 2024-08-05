import sys
import os
import json
from pathlib import Path
from logbook import Logger, StreamHandler

from python_postman.config import Request
from python_postman.config import PostmanCollection
from python_postman.template import CustomTemplate

StreamHandler(sys.stdout).push_application()
logger = Logger(name="MESSAGE")


class Collection:
    def __init__(self, collection_file: str) -> None:
        with open(Path(collection_file)) as file:
            text = file.read().replace("{{", "${").replace("}}", "}")
            collection_json = json.loads(text)
            collection_variables = {
                var["key"]: var["value"]
                for var in collection_json.get("variable", [])
                if not var.get("disabled", False)
            }
            template: str = CustomTemplate(template=text).safe_substitute(
                collection_variables
            )  # -> Collection variables are applied first. Disable variable in [Postman Variables] if it needs to be skipped.
            template: str = CustomTemplate(template=template).safe_substitute(
                os.environ
            )  # -> Environment variables are applied second. Remove [Environment Variable] if it needs to be skipped.
            __auth_data: dict = json.loads(template)
            __auth_collection: PostmanCollection = PostmanCollection(**__auth_data)
            self._auth = (
                __auth_collection.auth
            )  # -> Auth variables are set with [Collection Variables or Environment Variables] only. [Environmen Variables] are highly recommended.
            data: dict = json.loads(text)

        __postman_collection = PostmanCollection(**data)
        self._info = __postman_collection.info
        self._variables = (
            __postman_collection.variables
        )  # -> Apply collection variables to the requests.
        self._items = (
            __postman_collection.items
        )  # This object returns the Collection root items [folders & requests] only.
        self._requests = __postman_collection.requests

    def get_request(self, name: str) -> Request:
        requests = []
        for request in self._requests:
            if name == request.name:
                if request.events:
                    request.prerequest = request.events[0]
                    request.test = request.events[1]
                requests.append(request)

        if not requests:
            logger.error(f"Request name {name} not found in the collection.")
            raise ValueError(f"No request found with the {name=}")

        if len(requests) > 1:
            logger.error(f"Multiple requests found with the name {name=}")
            raise ValueError("Please ensure that the Postman request names are unique.")

        return requests[0]
