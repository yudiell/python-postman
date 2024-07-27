import os
import json
import re
from requests import Session, Response
from urllib3 import Timeout

from ..request import Request as CollectionRequest
from ..template import CustomTemplate
from .logger import Log


class Request(Session):
    def __init__(
        self,
        request: CollectionRequest,
        timeout: Timeout = Timeout(connect=15, read=60),
        stream: bool = True,
    ) -> None:
        super().__init__()
        self._request: CollectionRequest = request
        self.log: Log = Log()
        self.timeout: Timeout = timeout
        self.stream: bool = stream
        self.url: str = self._request.url.base_url
        self.body = None
        self.prepare_cookies = None

    def set_headers(self, headers: dict):
        """
        Set the headers of the request.

        Args:
            headers (dict): The headers to set.

        Returns:
            None
        """
        if self._request.headers:
            text = json.dumps(self._request.headers.as_dict)
            template: str = CustomTemplate(text).safe_substitute(headers)
            headers = {
                key: value
                for key, value in json.loads(template).items()
                if "${" not in value
            }
            self.headers = headers

    def set_params(self, params: dict):
        """
        Set URL parameters on the request object.

        Args:
            params (dict): Parameters to set on the request object.

        Returns:
            None
        """
        if self._request.url.params:
            text = json.dumps(self._request.url.params)
            template: str = CustomTemplate(text).safe_substitute(params)
            params = {
                key: value
                for key, value in json.loads(template).items()
                if "${" not in value
            }
            self.params = params

    def set_path_vars(self, path_variables: dict):
        """
        This function sets the path variables for a given request.

        Parameters:
            path_variables (dict): The data to be substituted into the url template.

        Returns:
            None
        """
        if self._request.url.base_url:
            request_url = self._request.url.base_url
            path: str = CustomTemplate(request_url).safe_substitute(path_variables)
            self.url = path

    def set_body(self, body: dict, with_quuotes: bool = True):
        """
        Set body payload.

        Args:
            body (dict): Parameters to set on the request object.
            with_quotes (bool) default=True: Add/remove quotes on body parameters.
        Returns:
            None
        """
        # The pattern looks for ${...} that's not surrounded by quotes
        pattern = r'(?<!")(\$\{[^}]+\})(?!")'
        # Replacement pattern that adds quotes around the matched pattern
        if with_quuotes:
            replacement = r'"\1"'
        else:
            replacement = r"\1"
        raw = (
            re.sub(pattern, replacement, self._request.body.raw)
            if self._request.body.raw
            else None
        )

        formdata = (
            json.dumps(self._request.body.formdata_as_dict)
            if self._request.body.formdata_as_dict
            else None
        )

        urlencoded = (
            json.dumps(self._request.body.urlencoded_as_dict)
            if self._request.body.urlencoded_as_dict
            else None
        )

        options_list = [
            formdata,
            urlencoded,
        ]
        options = next(
            (option for option in options_list if option is not None),
            ModuleNotFoundError,
        )
        if self._request.body.formdata or self._request.body.urlencoded:
            text = options
            template: str = CustomTemplate(text).safe_substitute(body)
            items = {
                key: value
                for key, value in json.loads(template).items()
                if "${" not in value
            }
            self.body = items
        else:
            substitute_body: str = CustomTemplate(raw).safe_substitute(body)
            self.body = substitute_body

    def substitute_bearer_token(self) -> None:
        if self._request.auth and self._request.auth.type == "bearer":
            self._request.auth.http_auth.token = CustomTemplate(
                self._request.auth.http_auth.token
            ).safe_substitute(os.environ)

    @property
    def send(self) -> Response:
        log: Log = self.log
        with Session() as session:
            # Setting the requests
            request: CollectionRequest = self._request
            log.info(f"Request Name: {request.name}")

            # Substitute the a bearer token at the API call level.
            # This is a substitution for the postman "test" script that sets a bearer token.
            self.substitute_bearer_token()

            # Setting the request params
            method = request.method
            url = self.url
            headers = self._request.headers.as_dict
            params = self.params
            data = self.body
            timeout = self.timeout
            stream = self.stream
            auth = request.auth.http_auth
            prepare_cookies = self.prepare_cookies

            self.log.request(url=url)
            response = session.request(
                auth=auth,
                method=method,
                url=url,
                headers=headers,
                params=params,
                data=data,
                stream=stream,
                timeout=timeout,
                cookies=prepare_cookies,
            )

            if response.ok:
                self.log.successful(url=url)
            else:
                self.log.raise_error(url=url, response=response)

            return response
