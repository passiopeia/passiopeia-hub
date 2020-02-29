"""
Request Objects
"""
from django.conf import settings

from hub_json_schema.schema.base.schema import JsonSchema
from hub_json_schema.schema.types import CredentialsTypeV1


class LoginRequestV1(JsonSchema):  # pylint: disable=too-few-public-methods
    """
    Login Request
    """

    schema_name = 'request-login'
    schema_version = 1

    schema_definition = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": '{}{}-v{}'.format(settings.JSON_SCHEMA_BASE, schema_name, schema_version),
        "title": schema_name,
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "credentials": {
                "$ref": '{}#/definitions/credentials'.format(CredentialsTypeV1.schema_definition.get('$id'))
            }
        }
    }

    example = {
        "credentials": {
            "username": "admin",
            "password": "password!",
            "otp": "123456",
        }
    }
