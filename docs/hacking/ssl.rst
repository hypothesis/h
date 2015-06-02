=================================
Serving h over SSL in development
=================================

If you want to annotate a site that's served over https then you'll need to
serve h over https as well, otherwise the browser will refuse to launch h and
give a mixed-content warning.

To serve your local dev instance of h over https:

1. Generate a private key and certificate signing request::

    openssl req -newkey rsa:1024 -nodes -keyout key.pem -out req.pem

2. Generate a self-signed certificate::

    openssl x509 -req -in req.pem -signkey key.pem -out server.crt

3. Run ``gunicorn`` with the ``certfile`` and ``keyfile`` options::

    gunicorn --reload --paste conf/development.ini --certfile=server.crt --keyfile=key.pem


---------------
Troubleshooting
---------------

Insecure Response errors in the console
=======================================

The sidebar fails to load and you see ``net::ERR_INSECURE_RESPONSE`` errors in
the console.  You need to open https://127.0.0.1:5000 and tell Chrome to allow
access to the site even though the certificate isn't known.
