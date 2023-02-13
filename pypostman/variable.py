import os
import pendulum
from string import Template

from .template import CustomTemplate
from .config import Variables


class Variables:
    def __init__(self, variables: Variables) -> None:
        # load_dotenv()
        self.variables = variables

    @property
    def as_dict(self):
        collection_variables = {}
        if self.variables:
            for variable in self.variables:
                collection_variables[variable.key] = variable.value
        # collection_variables.update(os.environ)
        return collection_variables

    @property
    def api_tags(self):
        """
        This property fetches the API tags associated with this object. It searches
        through the variables associated with the object and looks for keys called
        'API_TAGS', 'TAGS', or 'TAG'. If one of these is found, the associated value
        is split into a list by comma and returned. If none of these are found, an
        empty list is returned.
        """
        if self.variables:
            for variable in self.variables:
                if variable.key.upper() in ["API_TAGS", "TAGS", "TAG"]:
                    return variable.value.split(",")
        return []

    def s3_prefix(self, **kwargs):
        """
        This function takes in an environment string and returns the S3 prefix
        based on the provided environment and the current date. The S3 prefix is
        based on the variables stored in self.variables and is created using the
        CustomTemplate class.
        """
        if self.variables:
            for variable in self.variables:
                if variable.key.upper() in ["S3_PREFIX", "PREFIX"]:
                    s3_prefix = CustomTemplate(variable.value).safe_substitute(**kwargs)
                    return s3_prefix

    @property
    def model_name(self):
        """
        This function takes in an environment string and returns the S3 prefix
        based on the provided environment and the current date. The S3 prefix is
        based on the variables stored in self.variables and is created using the
        CustomTemplate class.
        """
        if self.variables:
            for variable in self.variables:
                if variable.key.upper() in ["MODEL_NAME", "MODEL"]:
                    return variable.value
