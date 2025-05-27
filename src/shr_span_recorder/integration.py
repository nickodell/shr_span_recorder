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
from shr_span_recorder.wsgi import SHRAwareSentryWsgiMiddleware


class SHRAwareDjangoIntegration(DjangoIntegration):
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
        print("in SHRAwareDjangoIntegration.setup_once!")
        # # type: () -> None

        # if DJANGO_VERSION < (1, 8):
        #     raise DidNotEnable("Django 1.8 or newer is required.")

        # install_sql_hook()
        # # Patch in our custom middleware.

        # # logs an error for every 500
        # ignore_logger("django.server")
        # ignore_logger("django.request")

        # Call superclass, then un-patch WSGI
        from django.core.handlers.wsgi import WSGIHandler

        wsgi_pre_patch = WSGIHandler.__call__
        # Patch everything else in Django
        DjangoIntegration.setup_once()
        # Un-patch WSGI handler
        WSGIHandler.__call__ = wsgi_pre_patch


        # Now patch the WSGI handler to use our middleware
        old_app = WSGIHandler.__call__

        @ensure_integration_enabled(SHRAwareDjangoIntegration, old_app)
        def sentry_patched_wsgi_handler(self, environ, start_response):
            # type: (Any, Dict[str, str], Callable[..., Any]) -> _ScopedResponse
            bound_old_app = old_app.__get__(self, WSGIHandler)

            from django.conf import settings

            use_x_forwarded_for = settings.USE_X_FORWARDED_HOST

            integration = sentry_sdk.get_client().get_integration(SHRAwareDjangoIntegration)

            use_shr_aware_wsgi_middleware = True
            if use_shr_aware_wsgi_middleware:
                middleware_class = SHRAwareSentryWsgiMiddleware
            else:
                middleware_class = SentryWsgiMiddleware

            middleware = middleware_class(
                bound_old_app,
                use_x_forwarded_for,
                span_origin=SHRAwareDjangoIntegration.origin,
                http_methods_to_capture=(
                    integration.http_methods_to_capture
                    if integration
                    else DEFAULT_HTTP_METHODS_TO_CAPTURE
                ),
            )
            return middleware(environ, start_response)

        WSGIHandler.__call__ = sentry_patched_wsgi_handler

        # _patch_get_response()

        # _patch_django_asgi_handler()

        # signals.got_request_exception.connect(_got_request_exception)

        # @add_global_event_processor
        # def process_django_templates(event, hint):
        #     # type: (Event, Optional[Hint]) -> Optional[Event]
        #     if hint is None:
        #         return event

        #     exc_info = hint.get("exc_info", None)

        #     if exc_info is None:
        #         return event

        #     exception = event.get("exception", None)

        #     if exception is None:
        #         return event

        #     values = exception.get("values", None)

        #     if values is None:
        #         return event

        #     for exception, (_, exc_value, _) in zip(
        #         reversed(values), walk_exception_chain(exc_info)
        #     ):
        #         frame = get_template_frame_from_exception(exc_value)
        #         if frame is not None:
        #             frames = exception.get("stacktrace", {}).get("frames", [])

        #             for i in reversed(range(len(frames))):
        #                 f = frames[i]
        #                 if (
        #                     f.get("function") in ("Parser.parse", "parse", "render")
        #                     and f.get("module") == "django.template.base"
        #                 ):
        #                     i += 1
        #                     break
        #             else:
        #                 i = len(frames)

        #             frames.insert(i, frame)

        #     return event

        # @add_global_repr_processor
        # def _django_queryset_repr(value, hint):
        #     # type: (Any, Dict[str, Any]) -> Union[NotImplementedType, str]
        #     try:
        #         # Django 1.6 can fail to import `QuerySet` when Django settings
        #         # have not yet been initialized.
        #         #
        #         # If we fail to import, return `NotImplemented`. It's at least
        #         # unlikely that we have a query set in `value` when importing
        #         # `QuerySet` fails.
        #         from django.db.models.query import QuerySet
        #     except Exception:
        #         return NotImplemented

        #     if not isinstance(value, QuerySet) or value._result_cache:
        #         return NotImplemented

        #     return "<%s from %s at 0x%x>" % (
        #         value.__class__.__name__,
        #         value.__module__,
        #         id(value),
        #     )

        # _patch_channels()
        # patch_django_middlewares()
        # patch_views()
        # patch_templates()
        # patch_signals()

        # if patch_caching is not None:
        #     patch_caching()
