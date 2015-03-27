HTTP API
========

This document details the ``h`` application's public HTTP API. It is targeted at
developers interested in integrating functionality from Hypothesis into their
own applications.


root
----

.. http:get:: /api

   API root. Returns hypermedia links to the rest of the API.

   **Example request**:

   .. sourcecode:: http

      GET /api
      Host: hypothes.is
      Accept: application/json


   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json; charset=UTF-8

      {
          "links": {
              "annotation": {
                  "create": {
                      "desc": "Create a new annotation",
                      "method": "POST",
                      "url": "https://hypothes.is/api/annotations"
                  },
                  "delete": {
                      "desc": "Delete an annotation",
                      "method": "DELETE",
                      "url": "https://hypothes.is/api/annotations/:id"
                  },
                  "read": {
                      "desc": "Get an existing annotation",
                      "method": "GET",
                      "url": "https://hypothes.is/api/annotations/:id"
                  },
                  "update": {
                      "desc": "Update an existing annotation",
                      "method": "PUT",
                      "url": "https://hypothes.is/api/annotations/:id"
                  }
              },
              "search": {
                  "desc": "Basic search API",
                  "method": "GET",
                  "url": "https://hypothes.is/api/search"
              }
          },
          "message": "Annotator Store API"
      }

   :reqheader Accept: desired response content type
   :resheader Content-Type: response content type
   :statuscode 200: no error


search
------

.. http:get:: /api/search

   Search for annotations.

   **Example request**:

   .. sourcecode:: http

      GET /api/search?limit=1000&user=gluejar@hypothes.is
      Host: hypothes.is
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json; charset=UTF-8

      {
          "rows": [
              {
                  "consumer": "00000000-0000-0000-0000-000000000000",
                  "created": "2014-01-12T18:36:15.697572+00:00",
                  "id": "LGVKq4E4SKKro1dBBEMwsA",
                  "permissions": { ... },
                  "references": ["6lkzoOubSOOymDNDIgazqw"],
                  "target": [],
                  "text": "Peut-etre",
                  "updated": "2014-01-12T18:36:15.697588+00:00",
                  "uri": "http://epubjs-reader.appspot.com//moby-dick/OPS/chapter_003.xhtml",
                  "user": "acct:gluejar@hypothes.is"
              }
          ],
          "total": 1
      }

   :query limit: number of results to return
   :query uri: limit results to annotations of `uri` (must be urlencoded)
   :query user: limit results to annotations created by `user`
   :query quote: limit results to annotations where quoted text contains `quote`
   :query text: limit results to annotations where body test contains `text`
   :reqheader Accept: desired response content type
   :resheader Content-Type: response content type
   :statuscode 200: no error
   :statuscode 400: errors parsing your query


read
----

.. http:get:: /api/annotations/(string:id)

   Retrieve a single annotation.

   **Example request**:

   .. sourcecode:: http

     GET /api/annotations/utalbWjUaZK5ifydnohjmA
     Host: hypothes.is
     Accept: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json; charset=UTF-8

      {
          "consumer": "00000000-0000-0000-0000-000000000000",
          "created": "2013-08-26T13:31:49.339078+00:00",
          "document": { ... },
          "id": "utalbWjUQZK5ifydnohjmA",
          "permissions": { ... },
          "references": [
              "ZkDZ8ZRXQkiEeG_3r7s1IA",
              "4uUTPORmTN-0y-puAXe_sw"
          ],
          "target": [],
          "text": "Dan, thanks for your team's work ...",
          "updated": "2013-08-26T14:09:14.121339+00:00",
          "uri": "http://example.com/foo",
          "user": "acct:johndoe@example.org"
      }

   :reqheader Accept: desired response content type
   :resheader Content-Type: response content type
   :statuscode 200: no error
   :statuscode 404: annotation with the specified `id` not found


create
------

.. http:post:: /api/annotations

   Create a new annotation. Requires a valid authentication token.

   **Example request**:

   .. sourcecode:: http

      POST /api/annotations
      Host: hypothes.is
      Accept: application/json
      Content-Type: application/json;charset=UTF-8
      X-Annotator-Auth-Token: eyJhbGc[...]mbl_YBM

      {
          "uri": "http://example.com/",
          "user": "acct:joebloggs@example.org",
          "permissions": {
              "read": ["group:__world__"],
              "update": ["acct:joebloggs@example.org"],
              "delete": ["acct:joebloggs@example.org"],
              "admin": ["acct:joebloggs@example.org"],
          },
          "document": { ... },
          "target": [ ... ],
          "tags": [],
          "text": "This is an annotation I made."
      }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json; charset=UTF-8

      {
          "id": "AUxWM-HasREW1YKAwhil",
          "uri": "http://example.com/",
          "user": "acct:joebloggs@example.org",
          ...
      }

   :param id: annotation's unique id
   :reqheader Accept: desired response content type
   :reqheader Content-Type: request body content type
   :reqheader X-Annotator-Auth-Token: JWT authentication token
   :resheader Content-Type: response content type
   :>json string id: unique id of new annotation
   :>json datetime created: created date of new annotation
   :>json datetime updated: updated date of new annotation (same as `created`)
   :statuscode 200: no error
   :statuscode 400: could not create annotation from your request (bad payload)
   :statuscode 401: no auth token was provided
   :statuscode 403: auth token provided does not convey "create" permissions


update
------

.. http:put:: /api/annotations/(string:id)

   Update the annotation with the given `id`. Requires a valid authentication
   token.

   **Example request**:

   .. sourcecode:: http

      PUT /api/annotations/AUxWM-HasREW1YKAwhil
      Host: hypothes.is
      Accept: application/json
      Content-Type: application/json;charset=UTF-8
      X-Annotator-Auth-Token: eyJhbGc[...]mbl_YBM

      {
          "uri": "http://example.com/foo",
      }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json; charset=UTF-8

      {
          "id": "AUxWM-HasREW1YKAwhil",
          "updated": "2015-03-26T13:09:42.646509+00:00"
          "uri": "http://example.com/",
          "user": "acct:joebloggs@example.org",
          ...
      }

   :param id: annotation's unique id
   :reqheader Accept: desired response content type
   :reqheader Content-Type: request body content type
   :reqheader X-Annotator-Auth-Token: JWT authentication token
   :resheader Content-Type: response content type
   :>json datetime updated: updated date of annotation
   :statuscode 200: no error
   :statuscode 400: could not update annotation from your request (bad payload)
   :statuscode 401: no auth token was provided
   :statuscode 403:
      auth token provided does not convey "update" permissions for the
      annotation with the given `id`
   :statuscode 404: annotation with the given `id` was not found


delete
------

.. http:delete:: /api/annotations/(string:id)

   Delete the annotation with the given `id`. Requires a valid authentication
   token.

   **Example request**:

   .. sourcecode:: http

      DELETE /api/annotations/AUxWM-HasREW1YKAwhil
      Host: hypothes.is
      Accept: application/json
      X-Annotator-Auth-Token: eyJhbGc[...]mbl_YBM

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json; charset=UTF-8

      {
          "deleted": true,
          "id": "AUxWM-HasREW1YKAwhil"
      }

   :param id: annotation's unique id
   :reqheader Accept: desired response content type
   :reqheader X-Annotator-Auth-Token: JWT authentication token
   :resheader Content-Type: response content type
   :>json boolean deleted: whether the annotation was deleted
   :>json string id: the unique `id` of the deleted annotation
   :statuscode 200: no error
   :statuscode 401: no auth token was provided
   :statuscode 403:
      auth token provided does not convey "update" permissions for the
      annotation with the given `id`
   :statuscode 404: annotation with the given `id` was not found
