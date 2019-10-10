Hypothesis Pyramid Sentry Extension
===================================

A small library intended to log messages to help [Sentry](https://sentry.io)
with the ability to filter out unwanted messages.

What should I use this for?
---------------------------

At the moment the library is mostly being used as an experimental testing
ground and therefore is not recommended for general use.

How it works
------------

In your Pyramid configuration you need to provide a list of filter functions
in the parameter `h_pyramid_sentry.filters`.

These functions are passed [Event](h_pyramid_sentry/event.py) objects which
they can inspect. If the function returns `True`, then the event is logged
locally, but not sent to Sentry

Usage
-----

```python
# Hook into Pyramid
config.add_settings({
    "h_pyramid_sentry.filters": [
        lambda event: instanceof(event.exception, ValueError)
    ],
    "h_pyramid_sentry.retry_support": True
})

config.include("h_pyramid_sentry")
```

Sentry configuration
--------------------

The Sentry integration will listen to the following Pyramid deployment settings:

| Pyramid setting        | Effect |
|------------------------|---------------|
| `h.sentry_environment` | Sets the Sentry option: [`environment`](https://docs.sentry.io/error-reporting/configuration/?platform=javascript#environment) |
| `h_pyramid_sentry.filters` | A list of functions to apply as filters |
| `h_pyramid_sentry.retry_support` | Enable retry detection and filtering |
