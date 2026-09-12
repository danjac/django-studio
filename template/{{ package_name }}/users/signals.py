"""Custom signals for the users app."""

from django.dispatch import Signal

# Sent before a user record is anonymised. Receivers get the User class as
# `sender` and the not-yet-anonymised instance as `user`, so they can still
# read the original PII (email, username) to clean up their own data.
pre_anonymise_user = Signal()

# Sent after a user record has been anonymised and allauth data removed.
# Same arguments; the instance's PII fields are already overwritten.
post_anonymise_user = Signal()
