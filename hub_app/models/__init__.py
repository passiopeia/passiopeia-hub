"""
Import all required models for the hub_app
"""
from .users import HubUser, BurnedOtp  # noqa: F401
from .registration import PendingRegistration  # noqa: F401
from .forgot_credentials import PendingCredentialRecovery  # noqa: F401
from .my_account import PendingEMailChange  # noqa: F401
