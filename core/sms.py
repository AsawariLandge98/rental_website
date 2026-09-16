"""Real, provider-agnostic SMS sending — same "scaffolding first, keys
later" pattern as core/validators.py's callers and the Razorpay/Google
OAuth/S3/Email blocks in settings.py.

No SMS gateway has been chosen yet (Feature 24 was explicitly scoped as
"build the scaffolding, decide the provider later"), and unlike SMTP email
there is no single standard protocol every provider speaks — each gateway
(MSG91, Twilio, Fast2SMS, ...) has its own request shape. Rather than guess
one specific provider's exact API contract, this sends a plain HTTP POST to
a fully configurable endpoint (SMS_API_URL) with the API key, sender ID,
recipient and message as both query params and form fields — the simple
shape shared by most basic REST SMS APIs. When a real provider is chosen,
only this one function needs adjusting to match its exact docs; nothing
else in the OTP flow (accounts/models.py::MobileOTP, accounts/views.py)
needs to change.

Until SMS_API_URL/SMS_API_KEY are added to .env, `settings.SMS_CONFIGURED`
is False and send_sms() never makes a network call — callers are expected
to check that flag first and fall back to a dev-safe path (see
accounts/views.py::mobile_verify_send), the same way the console email
backend keeps password reset testable with no real SMTP account.
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger('rentora.sms')


class SMSSendError(Exception):
    """Raised when a real SMS send attempt fails (gateway error, timeout,
    non-2xx response, etc). Never raised just because SMS isn't configured
    — check settings.SMS_CONFIGURED before calling send_sms() for that."""


def send_sms(mobile_number, message):
    """Send `message` to `mobile_number` via the configured SMS gateway.

    Raises SMSSendError on any failure. Callers must check
    settings.SMS_CONFIGURED before calling this — it does not fall back to
    a dev/console mode itself, so the caller's dev-mode branch stays an
    explicit, visible decision rather than something hidden in here."""
    if not settings.SMS_CONFIGURED:
        raise SMSSendError('SMS gateway is not configured.')

    payload = {
        'api_key': settings.SMS_API_KEY,
        'sender_id': settings.SMS_SENDER_ID,
        'mobile': mobile_number,
        'message': message,
    }
    try:
        response = requests.post(settings.SMS_API_URL, data=payload, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning('SMS send failed for %s: %s', mobile_number, exc)
        raise SMSSendError(str(exc)) from exc
