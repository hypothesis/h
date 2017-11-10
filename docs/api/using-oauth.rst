Using OAuth
###########

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
   back to the application (via a redirect or ``window.postMessage`` call).

4. The application exchanges the authorization code for a pair of tokens using
   the h service's ``POST /oauth/token`` endpoint: A short-lived access token to
   authorize API requests, and a long-lived refresh token.

5. When the access token expires, the application obtains a new access token
   using the ``POST /oauth/token`` endpoint.

To build an application for Hypothesis that uses OAuth, there are two steps:

1. Register an OAuth client for your application in the h service.

2. Implement the client-side part of the OAuth flow above in your application.
   Since OAuth is a widely implemented standard, there are many existing
   libraries for various languages which you can use.

.. _registering-an-oauth-client:

Registering an OAuth client
---------------------------

To register an OAuth client, go to the `/admin/oauthclients` page on the h
service. To register an OAuth client on the public h service at
https://hypothes.is, please contact us.

As an admin of the "h" service you can register a client for a browser-based
client:

1. Go to `/admin/oauthclients` and click "Register a new OAuth client".

2. Enter a name for a client, select "authorization_code" as the grant type and
   enter the URL where your client will listen for the authorization code as the
   "redirect URL".

3. Click "Register client" to create the client. Make a note of the randomly
   generated client ID.

.. _implementing-oauth-flow:

Implementing the OAuth flow
---------------------------

The h service implements the standard OAuth flow, with the following endpoints:

- Authorization page: ``GET /oauth/authorize``
- Token exchange: ``POST /oauth/token``
- Token refresh: ``POST /oauth/token``

See the `Authorization section
<https://aaronparecki.com/oauth-2-simplified/#authorization>`_ of "OAuth 2
simplified" for a description of how to implement the authorization flow for
different types of client.

Further reading
---------------

- `"OAuth 2 simplified" <https://aaronparecki.com/oauth-2-simplified/>`_ is a
  good introduction for developers.
- The `OAuth specification <https://tools.ietf.org/html/rfc6749>`_ describes the
  standard in detail.
