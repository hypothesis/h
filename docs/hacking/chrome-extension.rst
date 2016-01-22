=============================
Building the Chrome extension
=============================

This document describes how to build an instance of the
`Hypothesis Chrome extension`_ based on the current contents of your working
tree and install it in Chrome.

.. _Hypothesis Chrome extension: https://chrome.google.com/webstore/detail/hypothesis-web-pdf-annota/bjfhmglciegochdpefhhlphglcehbmek

---------------------------------------------
Building the Chrome extension for development
---------------------------------------------

To build and install the Chrome extension:

1. Do an :doc:`h development install </hacking/install>`.

2. Run this command to build the Chrome extension:

   .. code-block:: bash

      hypothesis-buildext chrome --debug --service 'http://127.0.0.1:5000'

   .. note::

      The ``--service`` URL specifies the Hypothesis service which the extension
      should communicate with. This can either point to your local H instance,
      if you have one set up, or the public instance at 'https://hypothes.is'.

      If you want to test the extension on pages served via HTTPS, you will
      need to configure the extension to communicate with a Hypothesis service
      that is **also served over HTTPS**. See :doc:`Serving h over SSL </hacking/ssl>`
      for instructions on serving a local instance of H via SSL.



3. Go to ``chrome://extensions/`` in Chrome.

4. Tick **Developer mode**.

5. Click **Load unpacked extension**.

6. Browse to the ``h/build/chrome/`` directory where the extension was built
   and select it.

Your extension should be working now! Remember that if you set ``--service``
to the URL of your local H instance, you need to have H running
in order to use the extension.

.. _Content Security Policy: http://en.wikipedia.org/wiki/Content_Security_Policy

---------------------------------------------
Building the Chrome extension for production
---------------------------------------------

For production builds of the Chrome extension, omit the ``--debug`` flag
and point it to a service which is served via `HTTPS`. You may also
wish to enable client error reporting by setting the ``--sentry-public-dsn``
argument.

.. code-block:: bash

   hypothesis-buildext chrome --service 'https://hypothes.is'

----------------------------------------------
Serving the sidebar from your local H instance
----------------------------------------------

In development, you may find it convenient to configure the extension
to load the sidebar app from the URL specified with ``--service`` instead
of bundling it into the extension. Building the extension this way
allows you to test changes to the sidebar code without having to re-run
the ``hypothesis-buildext`` command.

To do this, run ``hypothesis-buildext`` with the ``--no-bundle-sidebar``
flag.

There are issues with building the extension this way that you
should be aware of:

1. The extension will fail to load on ``https://`` pages unless
   the Hypothesis service specified with ``--service`` also
   uses an `https` URL.

2. The extension will fail to load on some sites that use
   `Content Security Policy`_. To test the extension on these sites
   you'll need to build without the ``--no-bundle-sidebar`` option.

---------------
Troubleshooting
---------------

Mixed Content errors in the console
===================================

The extension fails to load and you see *Mixed Content* errors in the console.
When using the Chrome extension on sites served over HTTPS, the extension
must be configured to use an HTTPS ``--service`` URL.


Insecure Response errors in the console
=======================================

You've built the extension with an ``https`` base URL, the extension fails to
load and you see ``net::ERR_INSECURE_RESPONSE`` errors in the console.
You need to open https://127.0.0.1:5000 (or whatever ``--service`` you gave)
and tell Chrome to allow access to the site even though the certificate isn't
known.


Content Security Policy errors in the console
=============================================

The extension fails to load and you see
*Refused to load the ... because it violates the following Content Security Policy directive: ...*
errors in the console.
See `Building the Chrome extension for production`_.


Empty Response errors in the console
====================================

The extension fails to load and you see
``GET http://127.0.0.:5000/... net::ERR_EMPTY_RESPONSE`` errors in the console.
This happens if you're running h on ``https`` but you've built the Chrome
extension with an ``http`` base URL. Either run h on ``http`` or rebuild the
extension with ``--service https://...``.


Connection Refused errors in the console
========================================

The extension fails to load and you see
``GET https://127.0.0.1:5000/... net::ERR_CONNECTION_REFUSED`` errors in the
console. This happens if you built the extension with an ``https`` service URL
but you're running h on ``http``. Either run h on ``https`` (see
:doc:`Run your local h instance using https </hacking/ssl>`)
or rebuild the extension  with ``--service http://...``.
