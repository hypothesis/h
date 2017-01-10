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

**This guide was last updated on 9 Jan 2017.**

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

    With a few important exceptions (see :ref:`memex`, below), these live in
    :py:mod:`h.models`.

Views (and templates)
    Views are code that is called in response to a particular request. Templates
    can be used to render the output of a particular view, typically as HTML.

    With a few exceptions, views live in :py:mod:`h.views`, and templates live
    in the ``h/templates/`` directory.

Services
    Putting business logic in views can quickly lead to views that are difficult
    to test. Putting business logic in models can lead to model objects with a
    large number of responsibilities.

    As such, we put most business logic into so-called "services." These are
    objects with behaviour and (optionally) state, which can be retrieved from
    the ``request`` object.

    Services live in :py:mod:`h.services`.

Tasks
    Tasks are bits of code that run in background workers and which can be
    easily triggered from within the context of a request.

    We use Celery_ for background tasks, and task definitions can be found in
    :py:mod:`h.tasks`.

There are a number of other modules and packages in the ``h`` repository. Some
of these (e.g. :py:mod:`h.auth`, :py:mod:`h.settings`) do one-off setup for a
booting application. Others may be business logic that dates from before we
introduced the `services pattern`_, and thus might be more appropriately moved
into a service in the future.

There is one important part of the ``h`` repository codebase that we haven't yet
talked about, and that's :ref:`memex`.

.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _Celery: http://www.celeryproject.org/
.. _services pattern: https://h.readthedocs.io/en/latest/arch/adr-002/

.. _memex:

-----
Memex
-----

The ``h`` web application is the software we use to run `our public web
annotation service`_. As such, it serves our organisational and operational
needs, and we aren't currently building it as if others will pick it up and use
it as-is. In order words, it's `coded in the open`_ rather than truly open
source.

With a view to releasing an important part of the software as true open-source
software that we support and which can be easily reused by others, the ``h``
repository also contains an installable Python package called ``memex``
alongside the main ``h`` application.

Memex is intended to be a Pyramid add-on which is responsible for storing
annotation data and exposing it over an HTTP API. We ourselves use memex to
provide part of the API for https://hypothes.is/.

Memex, as an installable package, lives in ``src/memex/``, and its installation
is controlled by ``setup.py`` in the repository root rather than by the
``requirements.*`` files used by ``h``.

As of early January 2017, we have not yet released a version of Memex to PyPI,
but we hope to in the near future.

.. _our public web annotation service: https://hypothes.is
.. _coded in the open: https://gds.blog.gov.uk/2012/10/12/coding-in-the-open/
