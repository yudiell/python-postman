from .config import Item
from .header import Headers
from .auth import Auth
from .body import Body
from .event import Events
from .url import Url


class Request:
    def __init__(self, item: Item) -> None:
        self.name: str = item.name
        self.events: Events = Events(events=item.events) if item.events else None
        self.method: str = item.request.method
        self.auth: Auth = Auth(auth=item.request.auth) if item.request.auth else None
        self.headers: Headers = Headers(headers=item.request.headers)
        self.body: Body = Body(body=item.request.body) if item.request.body else None
        self.url: Url = Url(url=item.request.url) if item.request.url else None
