Using OAuth
===========

`OAuth <https://en.wikipedia.org/wiki/OAuth>`_ is an open standard that enables
users to grant an application (an "OAuth client") the ability to interact with a
service as that user, but without providing their authentication credentials
(eg. username and password) directly to that application.

OAuth clients follow an authorization process, at the end of which they get an
access token which is included in API requests to the service. This process
works as follows:

1. The user clicks a login button or link in the application.

2. The application sends them to an authorization page from the h service
   (``/oauth/authorize``) via a redirect or popup, where the user will be
   asked to approve access.

3. If they approve, the authorization endpoint will send an authorization code
   back to the application (via a redirect).

4. The application exchanges the authorization code for a pair of tokens using
   the h service's ``POST /api/token`` endpoint: A short-lived access token to
   authorize API requests, and a long-lived refresh token.

5. When the access token expires, the application obtains a new access token
   by submitting the refresh token to the ``POST /api/token`` endpoint.

To build an application for Hypothesis that uses OAuth, there are two steps:

1. Register an OAuth client for your application in the h service.

2. Implement the client-side part of the OAuth flow above in your application.
   You may be able to use an existing OAuth 2 client library for your language
   and platform.

.. _registering-an-oauth-client:

Registering an OAuth client
---------------------------

To register an OAuth client on an instance of the h service for which you have
admin access, go to the `/admin/oauthclients` page. 

To register a new client as an admin of the "h" service:

1. Go to `/admin/oauthclients` and click "Register a new OAuth client".

2. Enter a name for a client, select "authorization_code" as the grant type and
   enter the URL where your client will listen for the authorization code as the
   "redirect URL".

3. Click "Register client" to create the client. Make a note of the randomly
   generated client ID.

.. _implementing-oauth-flow:

Implementing the OAuth flow
---------------------------

The h service implements the `"Authorization code grant"
<https://tools.ietf.org/html/rfc6749#section-4.1>`_ OAuth flow, with the
following endpoints:

- Authorization endpoint: ``/oauth/authorize``
- Token endpoint: ``/api/token``

In order to implement the flow, your application must do the following:

1. When a user clicks the "Login" link, the application should open the h
   service's authorization page at ``/oauth/authorize`` using the query
   parameters described in `4.1.1 Authorization Request
   <https://tools.ietf.org/html/rfc6749#section-4.1.1>`_.

   *Example request:*

   .. code-block:: http

      GET /oauth/authorize?client_id=510cd02e-767b-11e7-b34b-ebcff2e51409&redirect_uri=https%3A%2F%2Fmyapp.com%2Fauthorize&response_type=code&state=aa3d3062b4dbe0a1 HTTP/1.1

2. After the user authorizes the application, it will receive an authorization
   code via a call to the redirect URI. The application must exchange this code
   for an access token by making a request to the ``POST /api/token`` endpoint
   as described in `4.1.3 Access Token Request
   <https://tools.ietf.org/html/rfc6749#section-4.1.3>`_.

   *Example request:*

   .. code-block:: http

      POST /api/token HTTP/1.1
      Content-Type: application/x-www-form-urlencoded

      client_id=631206c8-7792-11e7-90b3-872e79925778&code=V1bjcvKDivRUc6Sg1jhEc8ckDwyLNG&grant_type=authorization_code

   *Example response:*

   .. code-block:: json

      {
        "token_type": "Bearer",
        "access_token": "5768-mfoPT52ogx0Si7NkU8QFicj183Wz1O4OQmbNIvBhjTQ",
        "expires_in": 3600,
        "refresh_token": "4657-dkJGNdVn8dmhDvgCHVPmIJ2Zi0cYQgDNb7RWXkpGIZs",
        "scope": "annotation:read annotation:write"
      }

3. Once the application has an access token, it can make API requests and
   connect to the real time API. See :doc:`authorization` for details of how
   to include this token in requests.
4. The access token expires after a while, and must be refreshed by making a
   request to the ``POST /api/token`` endpoint as described in `6. Refreshing
   an access token <https://tools.ietf.org/html/rfc6749#section-6>`_.

   *Example request:*

   .. code-block:: http

      POST /api/token HTTP/1.1
      Content-Type: application/x-www-form-urlencoded

      grant_type=refresh_token&refresh_token=4657-diyCpZ9oPRBaBkaW6ZrKgI0yagvZ9yBgLmxJ9k4HfeM

   *Example response:*

   .. code-block:: json

      {
        "token_type": "Bearer",
        "access_token": "5768-8CHodeMUAPCLmuBooabXolnpHReBUI5cC3txCXk7sQA",
        "expires_in": 3600,
        "refresh_token": "4657-11f1CUrhZs29QvXpywDpsXFwlfl_wPEIY5N8whwUrRw",
        "scope": "annotation:read annotation:write"
      }

Revoking tokens
---------------

If your application no longer needs an OAuth token, for example because a user
has logged out of your application which uses Hypothesis accounts, it is good
practice to revoke the access and refresh tokens.

Hypothesis implements the `OAuth 2 Token Revocation endpoint
<https://tools.ietf.org/html/rfc7009>`_ at ``/oauth/revoke``.

*Example request:*

.. code-block:: http

   POST /oauth/revoke HTTP/1.1
   Content-Type: application/x-www-form-urlencoded

   token=5768-yXoTA2R94b5fB0dTBbXHSvc_IX4I1Gc_bGQ4KyjM5dY

Further reading
---------------

- `"OAuth 2 simplified" <https://aaronparecki.com/oauth-2-simplified/>`_ is a
  good introduction for developers.
- The `OAuth specification <https://tools.ietf.org/html/rfc6749>`_ describes the
  standard in detail.
- The `OAuth Token Revocation specification <https://tools.ietf.org/html/rfc7009>`_
  describes an extension to support revoking tokens.
