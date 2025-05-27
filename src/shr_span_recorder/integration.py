# This file contains code from the sentry/sentry-python project, and is used under the MIT license

import sentry_sdk
from sentry_sdk.utils import (
    ensure_integration_enabled,
)
from sentry_sdk.integrations import Integration, DidNotEnable
from sentry_sdk.integrations.wsgi import SentryWsgiMiddleware

try:
    from django import VERSION as DJANGO_VERSION
    from django.conf import settings as django_settings
    from django.core import signals
    from django.conf import settings

    try:
        from django.urls import resolve
    except ImportError:
        from django.core.urlresolvers import resolve

    # Only available in Django 3.0+
    try:
        from django.core.handlers.asgi import ASGIRequest
    except Exception:
        ASGIRequest = None

except ImportError:
    raise DidNotEnable("Django not installed")


if DJANGO_VERSION[:2] > (1, 8):
    from sentry_sdk.integrations.django.caching import patch_caching
else:
    patch_caching = None  # type: ignore

from typing import TYPE_CHECKING

if TYPE_CHECKING:


    pass

from sentry_sdk.integrations.django import DjangoIntegration
from shr_span_recorder.consts import DEFAULT_HTTP_METHODS_TO_CAPTURE
from shr_span_recorder.wsgi import StreamAwareSentryWsgiMiddleware


class StreamAwareDjangoIntegration(DjangoIntegration):
    # Pretend to be the Django integration by setting identifier='django'
    # This has a few implications.
    #    1) If this integration is listed explictly in sentry_sdk.init(integrations=...), then
    #       the Django integration will not be loaded as a default integration.
    #    2) Integrations are deduplicated by identifier in sentry_sdk.setup_integrations(). If
    #       you list both this integration and DjangoIntegration, Sentry will only load the
    #       *last* integration with a duplicate identifier.
    #    3) Disabling DjangoIntegration through sentry_sdk.init(disabled_integrations=...) will
    #       also disable this Integration.
    #    4) A bunch of callbacks check if DjangoIntegration is loaded. If so, they will e.g.
    #       log a DB call. The easiest way to fake that is identifier='django'.
    #    5) Requests for settings on DjangoIntegration will use our Integration instead.
    identifier = 'django'

    @staticmethod
    def setup_once():
        # Save copy of WSGIHandler.__call__ before calling DjangoIntegration
        from django.core.handlers.wsgi import WSGIHandler
        wsgi_pre_patch = WSGIHandler.__call__

        # Patch everything else in Django
        # This instruments, e.g. middleware, databases, cache, etc.
        # We don't need to pass our configuration on, because DjangoIntegration will look up
        # the 'django' identifier in the list of integrations to get the configuration, and
        # that's us.
        # TODO: Fact check above statement
        DjangoIntegration.setup_once()

        # Un-patch WSGI handler. We need to add our own patch, and we don't want two transactions
        # for each HTTP request.
        WSGIHandler.__call__ = wsgi_pre_patch

        # Now patch the WSGI handler to use our middleware
        # Note: This is not middleware in the sense of Django's MIDDLEWARE setting - don't add
        # it there.
        old_app = WSGIHandler.__call__

        # This decorator is a low-overhead way to skip tracing if the Django integration is
        # not loaded.
        @ensure_integration_enabled(StreamAwareDjangoIntegration, old_app)
        def sentry_patched_wsgi_handler(self, environ, start_response):
            # type: (Any, Dict[str, str], Callable[..., Any]) -> _ScopedResponse
            bound_old_app = old_app.__get__(self, WSGIHandler)

            from django.conf import settings

            use_x_forwarded_for = settings.USE_X_FORWARDED_HOST

            integration = sentry_sdk.get_client().get_integration(StreamAwareDjangoIntegration)

            use_shr_aware_wsgi_middleware = True
            if use_shr_aware_wsgi_middleware:
                middleware_class = StreamAwareSentryWsgiMiddleware
            else:
                middleware_class = SentryWsgiMiddleware

            middleware = middleware_class(
                bound_old_app,
                use_x_forwarded_for,
                span_origin=StreamAwareDjangoIntegration.origin,
                http_methods_to_capture=(
                    getattr(integration, 'http_methods_to_capture', DEFAULT_HTTP_METHODS_TO_CAPTURE)
                    if integration
                    else DEFAULT_HTTP_METHODS_TO_CAPTURE
                ),
            )
            return middleware(environ, start_response)

        # Now patch WSGIHandler with our handler
        WSGIHandler.__call__ = sentry_patched_wsgi_handler
