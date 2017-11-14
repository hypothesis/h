Authorization
=============

API requests which only read public data do not require authorization.

API requests made as a particular user or which manage user accounts or groups
require authorization.

.. toctree::
   :maxdepth: 1

   using-oauth

Access tokens
-------------

API requests which read or write data as a specific user need to be authorized
with an access token. Access tokens can be obtained in two ways:

1. By generating a personal API token on the `Hypothesis developer
   page <https://hypothes.is/account/developer>`_ (you must be logged in to
   Hypothesis to get to this page). This is the simplest method, however
   these tokens are only suitable for enabling your application to make
   requests as a single specific user.

2. By :ref:`registering <registering-an-oauth-client>` an "OAuth client" and
   :ref:`implementing <implementing-oauth-flow>` the OAuth authentication flow
   in your application. This method allows any user to authorize your
   application to read and write data via the API as that user.  The Hypothesis
   client is an example of an application that uses OAuth.

   See :doc:`using-oauth` for details of how to implement this method.

Once an access token has been obtained, requests can be authorized by putting
the token in the ``Authorization`` header.

*Example request:*

..  code-block:: http

    GET /api HTTP/1.1
    Host: hypothes.is
    Accept: application/json
    Authorization: Bearer $TOKEN

(Replace ``$TOKEN`` with your own API token or OAuth access token.)

Client credentials
------------------

Endpoints for managing user accounts are authorized using a client ID and secret
("client credentials"). These can be obtained by :ref:`registering an OAuth
client <registering-an-oauth-client>` with the grant type set to
``client_credentials``.

Once a client ID and secret have been obtained, requests are authorized using
HTTP Basic Auth, where the client ID is the username and the client secret is
the password.

For example, with client details as follows

..  code-block:: bash

    Client ID: 96653f8e-80be-11e6-b32b-c7bcde86613a
    Client Secret: E-hReVMuRyZbyr1GikieEw4JslaM6sDpb18_9V59PFw

you can compute the Authorization header [as described in
RFC7617](https://tools.ietf.org/html/rfc7617):

..  code-block:: bash

    $ echo -n '96653f8e-80be-11e6-b32b-c7bcde86613a:E-hReVMuRyZbyr1GikieEw4JslaM6sDpb18_9V59PFw' | base64
    OTY2NTNmOGUtODBiZS0xMWU2LWIzMmItYzdiY2RlODY2MTNhOkUtaFJlVk11UnlaYnlyMUdpa2llRXc0SnNsYU02c0RwYjE4XzlWNTlQRnc=

*Example request:*

..  code-block:: http

    POST /users HTTP/1.1
    Host: hypothes.is
    Accept: application/json
    Content-Type: application/json
    Authorization: Basic OTY2NTNmOGUtODBiZS0xMWU2LWIzMmItYzdiY2RlODY2MTNhOkUtaFJlVk11UnlaYnlyMUdpa2llRXc0SnNsYU02c0RwYjE4XzlWNTlQRnc=

    {
      "authority": "example.com",
      "username": "jbloggs1",
      "email": "jbloggs1@example.com"
    }

