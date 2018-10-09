=================================
Serving h over SSL in development
=================================

If you want to annotate a site that's served over HTTPS then you'll need to
serve h over HTTPS as well, since the browser will refuse to load external
scripts (eg. H's bookmarklet) via HTTP on a page served via HTTPS.

To serve your local dev instance of h over HTTPS:

1. Generate a private key and certificate signing request::

    openssl req -newkey rsa:1024 -nodes -keyout .tlskey.pem -out .tlscsr.pem

2. Generate a self-signed certificate::

    openssl x509 -req -in .tlscsr.pem -signkey .tlskey.pem -out .tlscert.pem

3. Run ``hypothesis devserver`` with the ``--https`` option::

    tox -e py27-dev -- sh bin/hypothesis devserver --https

4. Since the certificate is self-signed, you will need to instruct your browser to
   trust it explicitly by visiting https://localhost:5000 and selecting the option
   to bypass the validation error.

---------------
Troubleshooting
---------------

Insecure Response errors in the console
=======================================

The sidebar fails to load and you see ``net::ERR_INSECURE_RESPONSE`` errors in
the console.  You need to open https://localhost:5000 and tell the browser to allow
access to the site even though the certificate isn't known.


Server not found, the connection was reset
==========================================

When you're serving h over SSL in development making non-SSL requests to h
won't work.

If you get an error like **Server not found** or **The connection was reset**
in your browser (it varies from browser to browser), possibly accompanied by a
gunicorn crash with
``AttributeError: 'NoneType' object has no attribute 'uri'``, make sure that
you're loading https://localhost:5000 in your browser, not ``http://``.


WebSocket closed abnormally, code: 1006
=======================================

If you see the error message
**Error: WebSocket closed abnormally, code: 1006** in your browser,
possibly accompanied by another error message like
**Firefox can't establish a connection to the server at wss://localhost:5001/ws**,
this can be because you need to add a security exception to allow your browser
to connect to the websocket. Visit https://localhost:5001 in a browser tab and
add a security exception then try again.


403 response when connecting to WebSocket
=========================================

If your browser is getting a 403 response when trying to connect to the
WebSocket along with error messages like these:

* WebSocket connection to 'wss://localhost:5001/ws' failed: Error during WebSocket handshake: Unexpected response code: 403
* Check that your H service is configured to allow WebSocket connections from https://127.0.0.1:5000
* WebSocket closed abnormally, code: 1006
* WebSocket closed abnormally, code: 1001
* Firefox can't establish a connection to the server at wss://localhost:5001/ws

make sure that you're opening https://localhost:5000 in your browser and
*not* https://127.0.0.1:5000.
