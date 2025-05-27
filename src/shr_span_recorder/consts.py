# This file contains code from the sentry/sentry-python project, and is used under the MIT license
# Shared constants

DEFAULT_HTTP_METHODS_TO_CAPTURE = (
    "CONNECT",
    "DELETE",
    "GET",
    # "HEAD",  # do not capture HEAD requests by default
    # "OPTIONS",  # do not capture OPTIONS requests by default
    "PATCH",
    "POST",
    "PUT",
    "TRACE",
)
