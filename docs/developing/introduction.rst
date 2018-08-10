=================================
An introduction to the h codebase
=================================

If you're new to the team, or to the Hypothesis project, you probably want to
get up to speed as quickly as possible so you can make meaningful improvements
to ``h``. This document is intended to serve as a brief "orientation guide" to
help you find your way around the codebase.

This document is a living guide, and is at risk of becoming outdated as we
continually improve the software. If you spot things that are out of date,
please submit a pull request to update this document.

**This guide was last updated on 11 Apr 2017.**

----------------------------
A lightning guide to Pyramid
----------------------------

The ``h`` codebase is principally a Pyramid_ web application. Pyramid is more of
a library of utilities than a "framework" in the sense of Django or Rails. As
such, the structure (or lack thereof) in our application is provided by our own
conventions, and not the framework itself.

Important things to know about Pyramid that may differ from other web
application frameworks you've used:

- Application setup is handled explicitly by a distinct configuration step at
  boot. You'll note ``includeme`` functions in some modules -- these are part of
  that configuration system.
- The ``request`` object is passed into views explicitly rather than through a
  threadlocal (AKA "global variable"), and is often passed around explicitly to
  provide request context to other parts of the application. This has a number
  of advantages but can get a bit messy if not managed appropriately.

You can read more about the distinguishing features of Pyramid in the `excellent
Pyramid documentation`_.

.. _Pyramid: https://trypyramid.com
.. _excellent Pyramid documentation: http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/introduction.html

----------------------
Application components
----------------------

The important parts of the ``h`` application can be broken down into:

Models
    SQLAlchemy_ models representing the data objects that live in our database.
    These live in ``h.models``.

Views (and templates)
    Views are code that is called in response to a particular request. Templates
    can be used to render the output of a particular view, typically as HTML.

    With a few exceptions, views live in ``h.views``, and templates live
    in the ``h/templates/`` directory.

Services
    Putting business logic in views can quickly lead to views that are difficult
    to test. Putting business logic in models can lead to model objects with a
    large number of responsibilities.

    As such, we put most business logic into so-called "services." These are
    objects with behaviour and (optionally) state, which can be retrieved from
    the ``request`` object.

    Services live in ``h.services``.

Tasks
    Tasks are bits of code that run in background workers and which can be
    easily triggered from within the context of a request.

    We use Celery_ for background tasks, and task definitions can be found in
    ``h.tasks``.

There are a number of other modules and packages in the ``h`` repository. Some
of these (e.g. ``h.auth``, ``h.settings``) do one-off setup for a
booting application. Others may be business logic that dates from before we
introduced the `services pattern`_, and thus might be more appropriately moved
into a service in the future.

.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _Celery: http://www.celeryproject.org/
.. _services pattern: https://h.readthedocs.io/en/latest/arch/adr-002/

