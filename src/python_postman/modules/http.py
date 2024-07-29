import os
import json
import re
from requests import Session, Response
from urllib3 import Timeout
from typing import Optional, Dict, Any

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

    def set_body(self, body: Optional[Dict[str, Any]] = None) -> None:
        if not hasattr(self._request, "body") or self._request.body is None:
            self.log.info("Request does not have a body. Skipping body setting.")
            return

        if body is None:
            self.log.info("Provided body is None. Skipping body setting.")
            return

        try:
            if self._request.body.raw:
                self._set_raw_body(self._request.body.raw, body)
            elif self._request.body.formdata_as_dict:
                self._set_form_data(self._request.body.formdata_as_dict, body)
            elif self._request.body.urlencoded_as_dict:
                self._set_form_data(self._request.body.urlencoded_as_dict, body)
            else:
                self.log.warning("Request body is empty or in an unsupported format.")
        except AttributeError as e:
            self.log.error(f"Unexpected attribute error while setting body: {e}")
        except Exception as e:
            self.log.error(f"An error occurred while setting the body: {e}")

    def _set_raw_body(self, raw: str, body: Dict[str, Any]) -> None:
        template = CustomTemplate(raw)
        substituted = template.safe_substitute(body)

        def replace_value(match):
            value = match.group(1) or match.group(2)
            return {"True": "true", "False": "false", "None": "null"}.get(value, value)

        # Replace placeholders and handle boolean/null values in one pass
        parsed = re.sub(
            r"\$\{([^}]+)\}|\b(True|False|None)\b", replace_value, substituted
        )

        try:
            # Ensure the result is valid JSON
            json_obj = json.loads(parsed)
            self.body = json.dumps(json_obj)
        except json.JSONDecodeError:
            self.log.error(f"Invalid JSON after substitution: {parsed}")
            self.body = parsed

    def _set_form_data(self, data: Dict[str, Any], body: Dict[str, Any]) -> None:
        try:
            template = CustomTemplate(json.dumps(data))
            substituted = template.safe_substitute(body)
            self.body = json.loads(substituted)
        except json.JSONDecodeError as e:
            self.log.error(f"JSON decode error in _set_form_data: {e}")
        except KeyError as e:
            self.log.error(f"Missing key in body dictionary: {e}")
        except Exception as e:
            self.log.error(f"An error occurred in _set_form_data: {e}")

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
