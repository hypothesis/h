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

The [EventFilter](h_pyramid_sentry/event_filter.py) object is a singleton
which you can register filter functions with. All functions registered to
the EventFilter object are global.

These functions are passed [Event](h_pyramid_sentry/event.py) objects which
they can inspect. If the function returns `True`, then the event is logged
locally, but not sent to Sentry

Usage
-----

To load the basic integration, in your Pyramid app config add:

    # Hook into Pyramid
    config.include("h_pyramid_sentry")

To set some custom filters to exclude certain errors from logging to Sentry:

    from h_pyramid_sentry import EventFilter

    EventFilter.set_filters([
        # Filter out ValueErrors
        lambda event: instanceof(event.exception, ValueError)
    ]])

Sentry configuration
--------------------

The Sentry integration will listen to the following Pyramid deployment settings:

| Pyramid setting        | Sentry option |
|------------------------|---------------|
| `h.sentry_environment` | [`environment`](https://docs.sentry.io/error-reporting/configuration/?platform=javascript#environment) |
