from typing import Dict, List
from .config import Header


class Headers:
    def __init__(self, headers: List[Header]) -> None:
        self.headers = headers

    @property
    def as_dict(self) -> Dict[str, str]:
        if not self.headers:
            return None

        headers = {}
        for header in self.headers:
            if not header.disabled:
                headers[header.key] = header.value
        return headers
