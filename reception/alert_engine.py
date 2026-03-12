from django.utils import timezone
from datetime import timedelta
from .models import Token
from .sms_service import send_sms


def send_upcoming_alerts():

    now = timezone.now()

    tokens = Token.objects.filter(
        status="WAITING",
        alert_message_sent=False
    )

    for token in tokens:

        alert_time = token.billing_expected_time - timedelta(minutes=5)

        if now >= alert_time:

            message = f"""
Your billing will start around {token.billing_expected_time.strftime('%H:%M')}.
Please come near the pharmacy counter.
"""

            send_sms(token.patient.phone, message)

            token.alert_message_sent = True
            token.save()