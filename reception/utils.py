from twilio.rest import Client
from django.conf import settings


# 🔹 TOKEN CREATED SMS
def send_token_sms(patient_phone, token_number, billing_time):

    client = Client(
        settings.TWILIO_ACCOUNT_SID,
        settings.TWILIO_AUTH_TOKEN
    )

    message_body = f"""
Hospital Pharmacy Queue

Token Number: {token_number}
Expected Billing: {billing_time}

Please be near the counter.
"""

    client.messages.create(
        body=message_body,
        from_=settings.TWILIO_PHONE_NUMBER,
        to=patient_phone
    )


# 🔹 MEDICINE READY SMS (NEW FUNCTION)
def send_medicine_ready_sms(patient_phone, token_number, dispatch_time):

    client = Client(
        settings.TWILIO_ACCOUNT_SID,
        settings.TWILIO_AUTH_TOKEN
    )

    message_body = f"""
Hospital Pharmacy

Token Number: {token_number}

Your medicines are READY for pickup.

Please collect from the pharmacy counter.

Time: {dispatch_time}
"""

    client.messages.create(
        body=message_body,
        from_=settings.TWILIO_PHONE_NUMBER,
        to=patient_phone
    )