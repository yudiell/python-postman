import os
import json
from pathlib import Path

from .config import Config
from .variable import Variables
from .auth import Auth
from .event import Events
from .item import Items
from .template import CustomTemplate


class Collection:
    def __init__(self, collection_file) -> None:
        with open(Path(collection_file)) as file:
            text = file.read().replace("{{", "${").replace("}}", "}")
            template: str = CustomTemplate(text).safe_substitute(os.environ)
            data: dict = json.loads(template)

        self._template = template
        self._collection = Config(**data)
        self._info = self._collection.info
        self._variables: Variables = Variables(variables=self._collection.variables)
        self._auth: Auth = Auth(auth=self._collection.auth)
        self._events = Events(events=self._collection.events)
        self._test = self._events.test
        self._prerequest = self._events.prerequest
        self._items: Items = Items(items=self._collection.items)
        self._requests = self._items.requests()
        for request in self._requests:
            request.auth = self._auth if not request.auth else request.auth
            if request.url:
                template: str = CustomTemplate(request.url.base).safe_substitute(
                    self._variables.as_dict
                )
                request.url.base_url = template
