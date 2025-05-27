# Stream Aware Django Integration for Sentry

<!-- [![image](https://img.shields.io/pypi/v/shr_span_recorder.svg)](https://pypi.python.org/pypi/shr_span_recorder) -->

Record spans in Sentry even if they occur while the response is being streamed

## Installation

1.  Install this with the following command

    ```
    pip install git+https://github.com/nickodell/shr_span_recorder.git
    ```

2.  Add `StreamAwareDjangoIntegration()` to your integrations.

    Example:

    ```
    from shr_span_recorder import StreamAwareDjangoIntegration

    sentry_sdk.init(
        # ...
        integrations=[
            StreamAwareDjangoIntegration(),
        ],
    )
    ```

    If you have custom configuration for `DjangoIntegration()`, that can be passed to `StreamAwareDjangoIntegration()`. It understands all of the same options as `DjangoIntegration()`.

    ```
    import sentry_sdk
    from shr_span_recorder import StreamAwareDjangoIntegration

    sentry_sdk.init(
        # ...
        integrations=[
            StreamAwareDjangoIntegration(
                # Configuration for DjangoIntegration goes here. Any options that
                # StreamAwareDjangoIntegration does not understand are passed on
                # unmodified to DjangoIntegration
            ),
        ],
    )
    ```


3.  Remove `DjangoIntegration()` from integrations, if you have explicitly specified
    it.

    In other words, you should *not* do this:

    ```
    sentry_sdk.init(
        # ...
        integrations=[
            # WRONG WRONG WRONG
            StreamAwareDjangoIntegration(),
            # DO NOT MIX THESE
            DjangoIntegration(),
        ],
    )
    ```

    You should use one or the other. If you use both, Sentry will pick one of them to enable, and the other will be ignored.

4.  Remove Django from `disabled_integrations`, if you have explicitly disabled it.

    If `DjangoIntegration()` is disabled, this will also disable `StreamAwareDjangoIntegration()`.

    It is also not required to disable default integrations.

## Compatibility

-   Compatible with Sentry 2.12.0 to 2.29.1
-   I will probably not update this for Sentry 3.x - you're on your own
-   Compatibile with WSGI. ASGI probably doesn't work.

## Technical Details

This integration is a replacement for DjangoIntegration. It subclasses DjangoIntegration, and so it is able to provide all of the same features as DjangoIntegration. It differs in one major way. Specifically, when DjangoIntegration manages transactions, it begins transactions when calling your app, and ends when your app returns a value.

In contrast, this integration begins the transaction when calling your app, and ends the transaction when your app returns a value AND the WSGI server calls close() on that value.

As a fallback option, the transaction is also closed after five minutes, in case the WSGI server is refusing to close the transaction.

## Performance Note

The transaction timeout is implemented by spawning one thread per request. If your application must deal with a high volume of requests, consider whether this performance cost is prohibitive.

## License

This project is licensed under the MIT license.

## Not an Official Project

This project is not endorsed or approved by Functional Software, Inc, the owners of the Sentry trademark.
