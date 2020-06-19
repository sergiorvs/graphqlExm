from django.contrib.auth.tokens import PasswordResetTokenGenerator
from six import text_type
from .models import *


class TokenGenerator(PasswordResetTokenGenerator):

    def _make_hash_value(self, user, timestamp):
        num = TokenAux.objects.get(user=user).counter
        return (
                text_type(user.pk) + text_type(timestamp) +
                text_type(user.is_active) + text_type(num)
        )


account_activation_token = TokenGenerator()
change_password_token = TokenGenerator()
