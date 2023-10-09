from typing import Dict
from .config import Body


class Body:
    def __init__(self, body: Body) -> None:
        self.mode = body.mode
        self.raw = body.raw
        self.options = body.options
        self.formdata = body.formdata
        self.urlencoded = body.urlencoded

    @property
    def urlencoded_as_dict(self) -> Dict[str, str]:
        if not self.urlencoded:
            return None

        body = {}
        for option in self.urlencoded:
            if not option.get("disabled", False):
                body[option["key"]] = option["value"]
        return body

    @property
    def formdata_as_dict(self) -> Dict[str, str]:
        if not self.formdata:
            return None

        body = {}
        for option in self.formdata:
            if not option.get("disabled", False):
                body[option["key"]] = option["value"]
        return body
