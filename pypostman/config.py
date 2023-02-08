from typing import List, Dict, Optional
from pydantic import Field, BaseModel


class Info(BaseModel):
    postman_id: str = Field(None, alias="_postman_id")
    name: str
    postman_schema: str = Field(None, alias="schema")
    exporter_id: str = Field(None, alias="_exporter_id")


# Variable Related Objects
class Variables(BaseModel):
    key: Optional[str]
    value: Optional[str]
    type: Optional[str]
    disabled: Optional[str]


# Auth Related Objects
class AuthValues(BaseModel):
    key: str
    value: str
    type: str
    disabled: Optional[str]


class Auth(BaseModel):
    type: str
    noauth: Optional[List[AuthValues]]
    basic: Optional[List[AuthValues]]
    apikey: Optional[List[AuthValues]]
    bearer: Optional[List[AuthValues]]


# Collection and Request Related Objects
class Script(BaseModel):
    type: Optional[str]
    exec: List[str]


class Event(BaseModel):
    listen: Optional[str]
    script: Optional[Script]


# Request Related Objects
class Header(BaseModel):
    key: Optional[str]
    value: Optional[str]
    description: Optional[str]
    disabled: Optional[str]


class Variable(BaseModel):
    key: Optional[str]
    value: Optional[str]
    description: Optional[str]


class Param(BaseModel):
    key: Optional[str]
    value: Optional[str]
    description: Optional[str]
    disabled: Optional[str]


class Body(BaseModel):
    mode: Optional[str]
    raw: Optional[str]
    options: Optional[Dict[str, Dict[str, str]]]


class Url(BaseModel):
    raw: Optional[str]
    protocol: Optional[str]
    host: Optional[List[str]]
    path: Optional[List[str]]
    variable: Optional[List[Variable]]
    query: Optional[List[Param]]


class Request(BaseModel):
    auth: Optional[Auth]
    method: str
    headers: List[Header] = Field(None, alias="header")
    url: Optional[Url]
    body: Optional[Body]


# Collection Related Objects
class Item(BaseModel):
    name: str
    item: Optional[List["Item"]]
    events: Optional[List[Event]] = Field(None, alias="event")
    request: Optional[Request]

    @property
    def type(self):
        return "request" if self.request else "folder"


class Config(BaseModel):
    info: Optional[Info]
    items: Optional[List[Item]] = Field(None, alias="item")
    variables: Optional[List[Variables]] = Field(None, alias="variable")
    events: Optional[List[Event]] = Field(None, alias="event")
    auth: Optional[Auth]
