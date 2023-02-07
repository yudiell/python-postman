from .config import Event
from .config import Script


class Events:
    def __init__(self, events: Event) -> None:
        self.events = events

    @property
    def test(self) -> Script:
        if not self.events:
            return None

        for event in self.events:
            if event.listen == "test":
                return event.script

    @property
    def prerequest(self) -> Script:
        if not self.events:
            return None

        for event in self.events:
            if event.listen == "prerequest":
                return event.script

    def script_as_str(self, script: Script) -> str:
        if not script:
            return None
        return "".join(script.exec)
