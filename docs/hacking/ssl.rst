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

    hypothesis devserver --https

4. Since the certificate is self-signed, you will need to instruct your browser to
   trust it explicitly by visiting https://127.0.0.1:5000 and selecting the option
   to bypass the validation error.

---------------
Troubleshooting
---------------

Insecure Response errors in the console
=======================================

The sidebar fails to load and you see ``net::ERR_INSECURE_RESPONSE`` errors in
the console.  You need to open https://127.0.0.1:5000 and tell the browser to allow
access to the site even though the certificate isn't known.
