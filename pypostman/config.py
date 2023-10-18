from typing import List, Dict, Union, Optional
from pydantic import Field, BaseModel


class Info(BaseModel):
    postman_id: str = Field(None, alias="_postman_id")
    name: str
    postman_schema: str = Field(None, alias="schema")
    exporter_id: str = Field(None, alias="_exporter_id")


# Variable Related Objects
class Variables(BaseModel):
    key: Optional[str] = None
    value: Optional[str] = None
    type: Optional[str] = None
    disabled: Optional[bool] = None


# Auth Related Objects
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


# Collection and Request Related Objects
class Script(BaseModel):
    type: Optional[str] = None
    exec: List[str]


class Event(BaseModel):
    listen: Optional[str] = None
    script: Optional[Script] = None


# Request Related Objects
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
    auth: Optional[Auth] = None
    method: str
    headers: List[Header] = Field(None, alias="header")
    url: Optional[Url] = None
    body: Optional[Body] = None


# Collection Related Objects
class Item(BaseModel):
    name: str
    item: Optional[List["Item"]] = None
    events: Optional[List[Event]] = Field(None, alias="event")
    request: Optional[Request] = None

    @property
    def type(self):
        return "request" if self.request else "folder"


class Config(BaseModel):
    info: Optional[Info] = None
    items: Optional[List[Item]] = Field(None, alias="item")
    variables: Optional[List[Variables]] = Field(None, alias="variable")
    events: Optional[List[Event]] = Field(None, alias="event")
    auth: Optional[Auth] = None
