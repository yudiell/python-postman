from .config import Body


class Body:
    def __init__(self, body: Body) -> None:
        self.mode = body.mode
        self.raw = body.raw
        self.options = body.options
