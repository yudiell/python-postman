from typing import List

from .config import Item
from .request import Request


class Item:
    def __init__(self, item: Item) -> None:
        self.name = item.name
        self.item = item.item
        self.events = item.events
        self.request = item.request
        self.type = item.type


class Items:
    def __init__(self, items: List[Item]) -> None:
        self.items = items

    def requests(self) -> List[Request]:
        requests = []
        for item in self.items:
            if item.request:
                request = Request(item=item)
                requests.append(request)
            if item.item:
                requests.extend(Items(items=item.item).requests())
        return requests
