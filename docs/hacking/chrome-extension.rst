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

To build and install a local development instance of the Chrome extension:

1. Do an :doc:`h development install </hacking/install>`.

2. Run this command to build the Chrome extension:

   .. code-block:: bash

      hypothesis-buildext --debug conf/development.ini chrome --base 'http://127.0.0.1:5000'

   .. note::

      When you run the ``hypothesis-buildext`` command without a ``--assets``
      argument (as in the command above) it builds a Chrome extension
      configured to load its assets (JavaScript, CSS, ...) from the ``--base``
      URL (in the command above: your local development instance of the
      Hypothesis web app running at http://127.0.0.1:5000). That is: the web
      app serves these JavaScript, CSS and other files and the Chrome extension
      is configured to request them from the web app.

      This is the most convenient way to build the extension for development
      because you can make changes to these source files and have your changes
      take effect without having to re-run the ``hypothesis-buildext`` command.

      But there are some issues with building the extension this way that you
      should be aware of:

      1. The extension will fail to load on ``https://`` pages and you'll see a
         *mixed content* warning in the console. To test the extension on
         ``https`` sites see
         `Building an https version of the Chrome extension`_.

      2. The extension will fail to load on some sites that use
         `Content Security Policy`_. To test the extension on these sites see
         `Building the Chrome extension for production`_.

3. Go to ``chrome://extensions/`` in Chrome.

4. Tick **Developer mode**.

5. Click **Load unpacked extension**.

6. Browse to the ``h/build/chrome/`` directory where the extension was built
   and select it.

Your extension should be working now! Remember that it communicates with your
local h instance, so you need to have h running to use the extension.

.. _Content Security Policy: http://en.wikipedia.org/wiki/Content_Security_Policy

-------------------------------------------------
Building an https version of the Chrome extension
-------------------------------------------------

To use the Chrome extension on ``https`` sites you need to serve the
extension's assets over ``https``:

1. :doc:`Run your local h instance using https </hacking/ssl>`.

2. Build the extension with an ``https`` base URL:

   .. code-block:: bash

      hypothesis-buildext --debug conf/development.ini chrome --base 'https://127.0.0.1:5000'

3. Follow steps 3-6 from `Building the Chrome extension for development`_
   above to install the extension in Chrome. (If you've already installed the
   extension and you just rebuilt it for ``https`` then you don't need to do
   anything.)

Your extension should now work on ``https`` sites.


--------------------------------------------
Building the Chrome extension for production
--------------------------------------------

The production Chrome extension doesn't load its assets from a website. Instead
we pack the asset files into the extension itself and it loads them from
``chrome-extension://`` URLs. This makes the extension faster and means that it
works on sites whose `Content Security Policy`_ would prevent assets from being
loaded from another site.

This method usually isn't convenient for development because you have to re-run
the ``hypothesis-buildext`` command after changing the source files for any of
the assets, but if you want to test the extension on a site that uses Content
Security Policy you should follow these steps:

1. Install some additional dependencies needed to build a production extension:

   .. code-block:: bash

      pip install -r requirements.txt

2. Follow  `Building an https version of the Chrome extension`_ above to build
   and install an ``https`` development extension.

3. Copy your extension's ID from the ``chrome://extensions`` page.
   Chrome generates this ID the first time you install the extension and will
   reuse it each time your rebuild or reinstall the extension.

4. Rebuild the Chrome extension with packed assets, an ``https`` base URL, and
   using ``production.ini`` instead of ``development.ini``:

   .. code-block:: bash

      hypothesis-buildext conf/production.ini chrome
          --base   'https://127.0.0.1:5000'
          --assets 'chrome-extension://<id>/public'

   Replace ``<id>`` with the ID of your extension from the
   ``chrome://extensions`` page.

Your extension should now work on sites with ``https`` and Content Security
Policy.


---------------
Troubleshooting
---------------

Mixed Content errors in the console
===================================

The extension fails to load and you see *Mixed Content* errors in the console.
See `Building an https version of the Chrome extension`_.


Insecure Response errors in the console
=======================================

You've built the extension with an ``https`` base URL, the extension fails to
load and you see ``net::ERR_INSECURE_RESPONSE`` errors in the console.
You need to open https://127.0.0.1:5000 (or whatever ``--base`` you gave)
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
extension with ``--base https://...``.


Connection Refused errors in the console
========================================

The extension fails to load and you see
``GET https://127.0.0.1:5000/... net::ERR_CONNECTION_REFUSED`` errors in the
console. This happens if you built the extension with an ``https`` base URL
but you're running h on ``http``. Either run h on ``https`` (see
:doc:`Run your local h instance using https </hacking/ssl>`)
or rebuild the extension  with ``--base http://...``.


File Not Found errors in the console
====================================

The extension fails to load and you see ``net::ERR_FILE_NOT_FOUND`` errors in
the console. This can happen if you build the extension with
``conf/development.ini`` and ``--assets 'chrome-extension://<id>/public'``.
Packing assets is not supported with ``development.ini``, use
``conf/production.ini`` instead.
