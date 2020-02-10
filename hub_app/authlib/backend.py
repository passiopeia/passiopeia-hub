"""
Authentication Backend that incorporates a one-time password
"""
import datetime
from random import SystemRandom
from typing import Optional

from django.contrib.auth.backends import ModelBackend
from django.http import HttpRequest
from django.utils.timezone import now

from hub_app.authlib.crypt import SymmetricCrypt
from hub_app.authlib.totp.token import get_possible_otps
from hub_app.models.users import HubUser, BurnedOtp


class TotpAuthenticationBackend(ModelBackend):
    """
    Backend implementation for username, password and one-time password
    """

    @staticmethod
    def clean_username(username: str) -> str:
        """
        All our usernames should be lowercase without blanks around

        :param str username: The Username
        :rtype: str
        :returns: The cleaned username
        """
        return username.lower().strip()

    def authenticate(self, request: HttpRequest, username=None, password=None, one_time_pw=None) -> Optional[HubUser]:
        # pylint: disable=arguments-differ
        random = SystemRandom()
        for i in range(random.randrange(1, 5)):  # nosec
            HubUser().set_password('against-timing-attack' + str(i))  # Mitigation against timing attack
        if username is None or password is None or one_time_pw is None:
            return None
        if any(
                [len(username) < 1, len(username) > 150, len(password) < 1, len(password) > 1000, len(one_time_pw) != 6]
        ):
            return None
        c_user = TotpAuthenticationBackend.clean_username(username)
        user_object = super(TotpAuthenticationBackend, self).authenticate(request, c_user, password)  # type: HubUser
        if user_object is None:
            return None
        if user_object.totp_secret is None:
            return None
        possible_tokens = get_possible_otps(SymmetricCrypt().decrypt(user_object.totp_secret))
        if one_time_pw not in possible_tokens:
            return None
        current_time = now()
        starting_at = current_time - datetime.timedelta(hours=1)
        try:
            BurnedOtp.objects.filter(user=user_object, burned_timestamp__gte=starting_at).get(token=one_time_pw)
            return None
        except BurnedOtp.DoesNotExist:
            BurnedOtp.objects.create(user=user_object, token=one_time_pw)
        return user_object
