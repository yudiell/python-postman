import os
import json
from typing import List, Optional, Dict
from pydantic import Field, BaseModel
from pathlib import Path

from .template import CustomTemplate


class Variable(BaseModel):
    key: str
    value: str
    type: Optional[str]
    enabled: bool


class Environment(BaseModel):
    """
    Examples

    # Load Environment
    environment: Environment = Environment.load("environment.json")

    # Access Properties
    print(environment.id)  # Environment Id
    print(environment.name)  # Environment Name
    print(environment.variables[0].key)  # First Variable Key

    # As Dictionary
    variables_as_dict: dict = environment.variables_as_dict
    print(variables_as_dict)  # {'key': 'value'}
    """

    id: str
    name: str
    postman_variable_scope: str = Field(None, alias="_postman_variable_scope")
    postman_exported_at: str = Field(None, alias="_postman_exported_at")
    postman_exported_using: str = Field(None, alias="_postman_exported_using")
    variables: List[Variable] = Field(None, alias="values")

    def load(environment_file: str) -> "Environment":
        """
        Loads a Postman environment.json file.
        Replaces the postman {{var}} with a python ${var} ready for use with -
        string template.
        Replaces ${VAR} with os environment variables. The os env variables must match the ${VAR} name.
        Unpacs the environment json to an Environment.
        Returns an Environment Object.
        """
        assert (
            ".postman_environment.json" in environment_file
        ), f"File Error: {environment_file} - Please verify that you are using a postman_envrionment file."

        def replace(json_data: str) -> str:
            """
            This function takes a string of JSON data and replaces the the variable value
            with the variable key if the variable name is value -
            if the variable is enabled otherwise if the variable is disabled
            it will not be included in the return JSON data string.

            This behaviour is similar to the behaviour implemented on the Postman Envrironments

            Returns a JSON data string.
            """
            data: dict = json.loads(json_data)
            for variable in data["values"]:
                value = not variable["value"]
                is_enabled = bool(variable["enabled"])

                replace = all([value, is_enabled])

                if replace:
                    variable["value"] = f"""${{{variable["key"]}}}"""

                elif not is_enabled:
                    data["values"].remove(variable)

            return json.dumps(data)

        with open(Path(environment_file)) as file:
            json_data: str = file.read().replace("{{", "${").replace("}}", "}")
            text = replace(json_data=json_data)
            template: CustomTemplate = CustomTemplate(text).safe_substitute(os.environ)
            data: dict = json.loads(template)
            environment = Environment(**data)

            return environment

    @property
    def variables_as_dict(self) -> Dict[str, str]:
        """
        This property returns the environment as a -
        python dictionary.
        This dictionary is used when replacing the -
        required parameters in the Postman Collection.
        """
        variables: List[Variable] = self.variables
        variables_as_dict: dict = {}
        for variable in variables:
            variables_as_dict[variable.key] = variable.value
        return variables_as_dict
