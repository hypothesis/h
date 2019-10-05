:orphan:

Manually setting up the Hypothesis client integration
=====================================================

The `Hypothesis annotation client <https://github.com/hypothesis/client>`_
needs an OAuth client in order to request access tokens from h. In a
development environment this can be set up automatically by running ``make
devdata``. If you can't run ``make devdata``, or if you're setting up h in a
production environment, follow the instructions below to create an OAuth client
and configure the Hypothesis client to use it.

1. Create an OAuth client for the Hypothesis client:

   1. Log in to your h instance as an admin user and go to
      ``<YOUR_H_INSTANCE>/admin/oauthclients``
   2. Select "Register a new OAuth client"
   3. Choose a name (eg. "Client") and set the redirect URL to
      ``<YOUR_H_INSTANCE>/app.html``. Leave the other settings at their default
      values.
   4. After creating the client make a note of the randomly generated client
      ID, you'll need it for the next step.

2. Set the following environment variables to tell h to configure the
   Hypothesis client to use the OAuth client you just created:

   .. code-block:: sh

      export CLIENT_OAUTH_ID=<THE_CLIENT_ID_OF_THE_OAUTH_CLIENT_YOU_CREATED_ABOVE>
      export CLIENT_URL=<YOUR_CLIENT_URL>

In a development environment ``CLIENT_URL`` would be ``http://localhost:3001/hypothesis``.
See :envvar:`CLIENT_URL`.
