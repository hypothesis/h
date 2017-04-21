API demo
========

This is a small web application designed to demonstrate how to use the `memex`
package to create a Hypothesis-like JSON API for storing and retrieving
annotations.

In this example, the user list is hard-coded (see the top of `auth.py`). These
users can perform operations against the API. See below for examples.

Getting started
---------------

The demo assumes you have installed its prerequisites with:

    pip install -r requirements.txt

With all these installed, you can run the application with:

    ./run

Example usage
-------------

You can then use the annotations API by authenticating with HTTP Basic Auth. For
example, to create an annotation:

    $ curl -u alice:s3cret -XPOST 'http://localhost:8000/annotations' -d '{"uri": "http://example.com"}'
    {
      "id": "AVLqo0j-1FxWup_NehDM",
      "created": "2016-02-16T16:38:11.180250+00:00",
      "updated": "2016-02-16T16:38:11.180269+00:00",
      "user": "alice",
      "group": "__world__",
      "uri": "http://example.com",
      ...
    }
