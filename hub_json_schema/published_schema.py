"""
Which Schema Classes are published?
"""
from hub_json_schema.schema.requests import LoginRequestV1
from hub_json_schema.schema.types import UsernameTypeV1, PasswordTypeV1, OtpTypeV1, CredentialsTypeV1


PUBLISHED = (
    UsernameTypeV1, PasswordTypeV1, OtpTypeV1, CredentialsTypeV1,
    LoginRequestV1,
)
