# This file contains code from the sentry/sentry-python project, and is used under the MIT license
from sentry_sdk.scope import should_send_default_pii
from sentry_sdk.utils import AnnotatedValue


SENSITIVE_ENV_KEYS = (
    "REMOTE_ADDR",
    "HTTP_X_FORWARDED_FOR",
    "HTTP_SET_COOKIE",
    "HTTP_COOKIE",
    "HTTP_AUTHORIZATION",
    "HTTP_X_API_KEY",
    "HTTP_X_FORWARDED_FOR",
    "HTTP_X_REAL_IP",
)

SENSITIVE_HEADERS = tuple(
    x[len("HTTP_"):] for x in SENSITIVE_ENV_KEYS if x.startswith("HTTP_")
)


def _filter_headers(headers):
    # type: (Mapping[str, str]) -> Mapping[str, Union[AnnotatedValue, str]]
    if should_send_default_pii():
        return headers

    return {
        k: (
            v
            if k.upper().replace("-", "_") not in SENSITIVE_HEADERS
            else AnnotatedValue.removed_because_over_size_limit()
        )
        for k, v in headers.items()
    }
