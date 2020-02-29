"""
Types with the Hub Application
"""
from django.conf import settings

from hub_json_schema.schema.base.schema import JsonSchema


class UsernameTypeV1(JsonSchema):  # pylint: disable=too-few-public-methods
    """
    Type def for username
    """

    schema_name = 'type-username'
    schema_version = 1

    schema_definition = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": '{}{}-v{}'.format(settings.JSON_SCHEMA_BASE, schema_name, schema_version),
        "title": schema_name,
        "definitions": {
            "username": {
                "type": "string",
                "minLength": 3,
                "maxLength": 150,
                "pattern": r'^[\w.@+-]{3,150}$',
            }
        }
    }


class PasswordTypeV1(JsonSchema):  # pylint: disable=too-few-public-methods
    """
    Type def for password
    """

    schema_name = 'type-password'
    schema_version = 1

    schema_definition = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": '{}{}-v{}'.format(settings.JSON_SCHEMA_BASE, schema_name, schema_version),
        "title": schema_name,
        "definitions": {
            "password": {
                "type": "string",
                "minLength": 8,
                "maxLength": 1024,
            }
        }
    }


class OtpTypeV1(JsonSchema):  # pylint: disable=too-few-public-methods
    """
    Type def for OTP
    """

    schema_name = 'type-otp'
    schema_version = 1

    schema_definition = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": '{}{}-v{}'.format(settings.JSON_SCHEMA_BASE, schema_name, schema_version),
        "title": schema_name,
        "definitions": {
            "otp": {
                "type": "string",
                "minLength": 6,
                "maxLength": 6,
                "pattern": r'^[0-9]{6,6}$',
            }
        }
    }


class CredentialsTypeV1(JsonSchema):  # pylint: disable=too-few-public-methods
    """
    Type def for Credentials
    """

    schema_name = 'type-credentials'
    schema_version = 1

    schema_definition = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": '{}{}-v{}'.format(settings.JSON_SCHEMA_BASE, schema_name, schema_version),
        "title": schema_name,
        "definitions": {
            "credentials": {
                "type": "object",
                "required": ["username", "password", "otp"],
                "additionalProperties": False,
                "properties": {
                    "username": {
                        "$ref": '{}#/definitions/username'.format(UsernameTypeV1.schema_definition.get('$id'))
                    },
                    "password": {
                        "$ref": '{}#/definitions/password'.format(PasswordTypeV1.schema_definition.get('$id'))
                    },
                    "otp": {
                        "$ref": '{}#/definitions/otp'.format(OtpTypeV1.schema_definition.get('$id'))
                    }
                }
            }
        }
    }
