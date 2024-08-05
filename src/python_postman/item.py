from typing import List

from .config import Item as ConfigItem
from .request import Request


class Items:
    def __init__(self, items: List[ConfigItem]) -> None:
        self.items = items

    @property
    def requests(self) -> List[Request]:
        requests = []
        for item in self.items:
            if item.request:
                request = Request(item=item)
                requests.append(request)
            if item.item:
                requests.extend(Items(items=item.item).requests)
        return requests
