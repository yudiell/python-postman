from typing import Union, Optional, List, Dict, Any
from pydantic import Field, BaseModel


class Info(BaseModel):
    postman_id: str = Field(None, alias="_postman_id")
    name: str
    postman_schema: str = Field(None, alias="schema")
    exporter_id: str = Field(None, alias="_exporter_id")


class Variables(BaseModel):
    key: Optional[str] = None
    value: Optional[str] = None
    type: Optional[str] = None
    disabled: Optional[bool] = None


class AuthValues(BaseModel):
    key: str
    value: str
    type: str
    disabled: Optional[bool] = None


class Auth(BaseModel):
    type: str
    noauth: Optional[List[AuthValues]] = None
    basic: Optional[List[AuthValues]] = None
    apikey: Optional[List[AuthValues]] = None
    bearer: Optional[List[AuthValues]] = None


class Script(BaseModel):
    type: Optional[str] = None
    exec: List[str]


class Event(BaseModel):
    listen: Optional[str] = None
    script: Optional[Script] = None


class Header(BaseModel):
    key: Optional[str] = None
    value: Optional[str] = None
    description: Optional[str] = None
    disabled: Optional[bool] = None


class Variable(BaseModel):
    key: Optional[str] = None
    value: Optional[str] = None
    description: Optional[str] = None


class Param(BaseModel):
    key: Optional[str] = None
    value: Optional[str] = None
    description: Optional[str] = None
    disabled: Optional[bool] = None


class Body(BaseModel):
    mode: Optional[str] = None
    raw: Optional[str] = None
    formdata: Optional[List[Dict[str, Union[str, bool]]]] = None
    urlencoded: Optional[List[Dict[str, Union[str, bool]]]] = None
    options: Optional[Dict[str, Dict[str, Union[str, bool]]]] = None


class Url(BaseModel):
    raw: Optional[str] = None
    protocol: Optional[str] = None
    host: Optional[List[str]] = None
    path: Optional[List[str]] = None
    variable: Optional[List[Variable]] = None
    query: Optional[List[Param]] = None


class Request(BaseModel):
    name: Optional[str] = None
    auth: Optional[Auth] = None
    method: str
    headers: List[Header] = Field(default_factory=list, alias="header")
    url: Optional[Url] = None
    body: Optional[Body] = None
    events: Optional[List[Event]] = Field(None, alias="event")
    response: Optional[List[Any]] = None
    prerequest: Optional[Event] = Field(None, alias="prerequest")
    test: Optional[Event] = Field(None, alias="test")


class Item(BaseModel):
    name: str
    item: Optional[List["Item"]] = None
    events: Optional[List[Event]] = Field(None, alias="event")
    request: Optional[Request] = None
    response: Optional[List[Any]] = None


Item.model_rebuild()


class Items:
    def __init__(self, items: List[Item]) -> None:
        self.items = items

    @property
    def requests(self) -> List:
        requests = []
        for item in self.items:
            if item.request:
                item.request.name = item.name
                item.request.events = item.events
                item.request.response = item.response
                requests.append(item.request)
            if item.item:
                requests.extend(Items(items=item.item).requests)
        return requests


class PostmanCollection(BaseModel):
    info: Optional[Info] = None
    items: Optional[List[Item]] = Field(None, alias="item")
    variables: Optional[List[Variables]] = Field(None, alias="variable")
    events: Optional[List[Event]] = Field(None, alias="event")
    auth: Optional[Auth] = None

    @property
    def folders(self) -> Items:
        return Items(items=self.items)

    @property
    def requests(self) -> List:
        return self.folders.requests

    @property
    def collection_variables(self) -> Dict[str, str]:
        collection_variables = {}
        if self.variables:
            for variable in self.variables:
                collection_variables[variable.key] = variable.value
        return collection_variables
