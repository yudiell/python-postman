from typing import Dict, List

from .config import Url, Param, Variable


class Variable:
    def __init__(self, variable: Variable) -> None:
        self.key: str = variable.key
        self.value: str = variable.value
        self.description: str = variable.description


class Param:
    def __init__(self, param: Param) -> None:
        self.key: str = param.key
        self.value: str = param.value
        self.description: str = param.description
        self.disabled: str = param.disabled


class Url:
    def __init__(self, url: Url) -> None:
        self.raw: str = url.raw
        self.protocol: str = url.protocol
        self.host: str = url.host
        self.path: str = url.path
        self.variables: List[Variable] = url.variable
        self.query: List[Param] = url.query
        self.base_url: str = None

    @property
    def base(self) -> str:
        """
        This property returns a complete URL from the provided host and path.
        If no protocol is given, it defaults to 'https://'.
        Raises an AssertionError if no host or path are found in the postman collection.
        """
        assert self.host and self.path, print(
            "Error: No host or path were found in the postman collection."
        )
        protocol = f"{self.protocol}" if self.protocol else "https://"
        host = ".".join(self.host) + "/"
        path = "/".join(self.update_path())
        url = "".join([protocol, host, path])
        url = "".join([host, path])
        return url

    @property
    def params(self) -> Dict[str, str]:
        """
        A parameter is enabled/disabled in the Postman App.
        Enabled parameters are parameters that do not contain a "disabled: true" key: value
        returns a dictionary of enabled parameters.
        """
        if self.query:
            params: Dict = {}
            for param in self.query:
                param = Param(param=param)
                if not param.disabled:
                    params[param.key] = param.value
            return params

    @property
    def path_variables(self) -> Dict[str, str]:
        """
        A parameter is enabled/disabled in the Postman App.
        Enabled parameters are parameters that do not contain a "disabled: true" key: value
        returns a dictionary of enabled parameters.
        """
        if self.variables:
            variables: Dict = {}
            for variable in self.variables:
                variable = Variable(variable=variable)
                variables[variable.key] = variable.value
            return variables

    def update_path(self):
        """
        Update the path to replace each colon ":" with "${}"

        Args:
            self: The object itself

        Returns:
            path: The updated path
        """
        path = self.path
        for i, element in enumerate(path):
            if ":" in element:
                element = element.replace(":", "${")
                element = element + "}"
                self.path[i] = element

        return path
