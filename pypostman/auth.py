from requests.auth import HTTPBasicAuth, AuthBase

from .config import Auth as ConfigAuth


class BearerAuth(AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["Authorization"] = f"Bearer {self.token}"
        return r


class ApiKeyAuth(AuthBase):
    def __init__(self, apikey):
        self.apikey = apikey

    def __call__(self, r):
        """
        The postman collection auth determines
        where the apikey should be applied.
        1. Query: Is to be added to the query params.
        2. Header: Is to be added to the header.
        The postman collection auth apikey is to be applied to -
        the query params if the auth api key contains the key "in".
        """
        key = self.apikey["key"]
        value = self.apikey["value"]
        if self.apikey.get("in") is not None:
            r.prepare_url(url=r.url, params={key: value})
        else:
            r.headers[key] = value
        return r


class Auth:
    def __init__(self, auth: ConfigAuth):
        self.type = auth.type if auth else None
        self.__auth_config = (
            auth.noauth or auth.basic or auth.apikey or auth.bearer if auth else None
        )

        self.http_auth = (
            self.noauth or self.basic or self.apikey or self.bearer if auth else None
        )

    @property
    def noauth(self) -> None:
        if self.__auth_config and self.type == "noauth":
            return None

    @property
    def basic(self) -> HTTPBasicAuth:
        if self.__auth_config and self.type == "basic":
            basic = {}
            for item in self.__auth_config:
                basic[item.key] = item.value
            # print(basic)
            return HTTPBasicAuth(username=basic["username"], password=basic["password"])

    @property
    def apikey(self) -> ApiKeyAuth:
        if self.__auth_config and self.type == "apikey":
            apikey = {}
            for item in self.__auth_config:
                apikey[item.key] = item.value
            return ApiKeyAuth(apikey=apikey)

    @property
    def bearer(self) -> BearerAuth:
        if self.__auth_config and self.type == "bearer":
            bearer = {}
            for item in self.__auth_config:
                bearer[item.key] = item.value
            # print(bearer)
            return BearerAuth(token=bearer["token"])
