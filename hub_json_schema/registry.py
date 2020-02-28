"""
Registry for JSON Schema
"""
from hub_json_schema.schema import PUBLISHED


class Singleton(type):
    """
    Define a singleton Meta Class
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Registry(metaclass=Singleton):  # pylint: disable=too-few-public-methods
    """
    Define the singleton Registry
    """

    def __init__(self):
        """
        Initialize from the published classes
        """
        self.__registry = {}
        for schema in PUBLISHED:
            version = str(schema.schema_version)
            name = schema.schema_name
            if name not in self.__registry.keys():
                self.__registry[name] = {}
            if version in self.__registry[name]:  # pragma: no cover  # Only a safeguard during JSON Schema development
                raise ValueError('Duplicated JSON Schema Version: Name="{}", Version="{}"'.format(name, version))
            self.__registry[name][version] = schema.schema_definition

    @property
    def schemas(self):
        """
        Access to the Schema
        """
        return self.__registry
