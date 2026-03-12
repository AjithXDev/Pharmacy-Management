from datetime import timedelta
from .models import Token


def update_future_tokens(pharmacy, delayed_token, delay_seconds):

    tokens = Token.objects.filter(
        pharmacy=pharmacy,
        token_number__gt=delayed_token.token_number,
        status="WAITING"
    ).order_by("token_number")

    for token in tokens:

        if token.billing_expected_time:
            token.billing_expected_time += timedelta(seconds=delay_seconds)
            token.save()
        