from string import Template


class CustomTemplate(Template):
    idpattern = r"[a-z][\.\-_a-z0-9]*"
