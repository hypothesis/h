.. _Generating authorization grant tokens:

Generating authorization grant tokens
=====================================

.. warning::

   This document describes an integration mechanism that is undergoing
   early-stage testing. The details of the token format may change in the
   future.

In order to allow your users (i.e. those whose accounts and authentication
status you control) to annotate using a copy of Hypothesis embedded on your
pages, you can ask us to register your site as a special kind of OAuth client.

We will issue you with a :term:`Client ID` and a :term:`Client secret`. These
will allow you generate time-limited "authorization grant tokens" which can be
supplied as configuration to the Hypothesis sidebar, and which will allow your
users to annotate without needing to log in again. This document describes how
to generate those tokens.

Overview
--------

You will have been provided with the following:

.. glossary::

   Client ID
      A unique identifier for your client account. It's a UUID and will look
      something like this: ``4a2fa3b4-c160-4436-82d3-148f602c9aa8``

   Client secret
      A secret string which you MUST NOT reveal publicly, and which is used to
      cryptographically sign the grant tokens you will generate.

In addition, you will have provided us with what we call an "authority" for your
account. The authority is a DNS domain name and acts as a unique namespace for
your user's accounts. For example, if your site lives at
``https://example.com``, you may choose to use ``example.com`` as your
authority, although we do not currently require any particular correspondence
between your web address and your account authority.

You will use these three pieces of information, in combination with your user's
unique usernames, to generate the grant token.

The grant token is a `JSON Web Token (JWT) <https://jwt.io/>`_ and we strongly
recommend that you use an existing JWT library for your programming environment
if you can. You can find `a list of JWT client libraries here
<https://jwt.io/#libraries-io>`_.

Token format
------------

A grant token is a JWT, signed with the :term:`Client secret` using the
``HS256`` algorithm, with a payload in a specific format, given below. Let's
assume that:

- Your :term:`Client ID` is ``4a2fa3b4-c160-4436-82d3-148f602c9aa8``.
- Your authority is ``customwidgets.com``.
- The user has a username of ``samina.mian``.
- The current time is ``2016-11-08T11:35:45Z``, which corresponds to a UTC Unix
  timestamp of ``1478601345``.
- The token should be valid for a few minutes, e.g. until ``1478601645``,
  expressed as a UTC Unix timestamp. The server limits the lifetime of a token
  (the difference between the ``nbf`` and ``exp`` timestamps) to 10 minutes.
- The token should be valid for the annotation service running at
  ``hypothes.is``.

With these data, we can construct a token payload. It should look like the
following::

   {
     "aud": "hypothes.is",
     "iss": "4a2fa3b4-c160-4436-82d3-148f602c9aa8",
     "sub": "acct:samina.mian@customwidgets.com",
     "nbf": 1478601345,
     "exp": 1478601645
   }

You should sign this payload using the ``HS256`` JWT-signing algorithm, using
the :term:`Client secret` as the key. The result will look something like this::

   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI0QTJGQTNCNC1DMTYwLTQ0MzYtODJEMy0xNDhGNjAyQzlBQTgiLCJuYmYiOjE0Nzg2MDEzNDUsImF1ZCI6Imh5cG90aGVzLmlzIiwiZXhwIjoxNDc4NjAxOTQ1LCJzdWIiOiJhY2N0OnNhbWluYS5taWFuQGN1c3RvbXdpZGdldHMuY29tIn0.65-ZErbLu1q8LpT_K8FAOQO984hAyN1XFBe1rC3lgfk

.. seealso::

   `RFC7523 <https://tools.ietf.org/html/rfc7523>`_, "JSON Web Token (JWT)
   Profile for OAuth 2.0 Client Authentication and Authorization Grants". Note
   that we currently only support the ``HS256`` signing algorithm, and not the
   public-key ``RS256`` signing algorithm mentioned in the RFC.

Examples
--------

This section contains complete example code for generating a JWT in various
common programming environments.

Python
``````

We recommend using `PyJWT <https://pyjwt.readthedocs.io/en/latest/>`_::

   import datetime
   import jwt

   # IMPORTANT: replace these values with those for your client account!
   CLIENT_AUTHORITY = 'customwidgets.com'
   CLIENT_ID        = '4a2fa3b4-c160-4436-82d3-148f602c9aa8'
   CLIENT_SECRET    = '5SquUVG0Tpg57ywoxUbPPgjtK0OkX1ttipVlfBRRrpo'

   def generate_grant_token(username):
      now = datetime.datetime.utcnow()
      userid = 'acct:{username}@{authority}'.format(username=username,
                                                    authority=CLIENT_AUTHORITY)
      payload = {
         'aud': 'hypothes.is',
         'iss': CLIENT_ID,
         'sub': userid,
         'nbf': now,
         'exp': now + datetime.timedelta(minutes=10),
      }
      return jwt.encode(payload, CLIENT_SECRET, algorithm='HS256')

Ruby
````

We recommend using `ruby-jwt <https://jwt.github.io/ruby-jwt/>`_::

   require 'jwt'

   # IMPORTANT: replace these values with those for your client account!
   CLIENT_AUTHORITY = 'customwidgets.com'
   CLIENT_ID        = '4a2fa3b4-c160-4436-82d3-148f602c9aa8'
   CLIENT_SECRET    = '5SquUVG0Tpg57ywoxUbPPgjtK0OkX1ttipVlfBRRrpo'

   def generate_grant_token(username)
     now = Time.now.to_i
     userid = "acct:#{username}@#{CLIENT_AUTHORITY}"
     payload = {
       aud: "hypothes.is",
       iss: CLIENT_ID,
       sub: userid,
       nbf: now,
       exp: now + 600
     }
     JWT.encode payload, CLIENT_SECRET, 'HS256'
   end
