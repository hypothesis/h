====================
Source Documentation
====================

Reference material for the public APIs exposed is available in this section. It
It is targeted at developers interested in integrating functionality from
Hypothesis into their own Python applications. ::

    {
        "links": {
            "annotation": {
                "delete": {
                    "desc": "Delete an annotation", 
                    "method": "DELETE", 
                    "url": "https://hypothes.is/api/annotations/:id"
                }, 
                "update": {
                    "desc": "Update an existing annotation", 
                    "method": "PUT", 
                    "url": "https://hypothes.is/api/annotations/:id"
                }, 
                "create": {
                    "desc": "Create a new annotation", 
                    "method": "POST", 
                    "url": "https://hypothes.is/api/annotations"
                }, 
                "read": {
                    "desc": "Get an existing annotation", 
                    "method": "GET", 
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


--------------
API Endpoints:
--------------

/search
=======

Search for annotations annotations

Examples:

https://hypothes.is/api/search?limit=1000&uri=http%3A%2F%2Fepubjs-reader.appspot.com%2F%2Fmoby-dick%2FOPS%2Fchapter_003.xhtml&user=acct:gluejar@hypothes.is

https://hypothes.is/api/search?limit=1000&user=gluejar@hypothes.is

https://hypothes.is/api/search?limit=1000&quote=limber

https://hypothes.is/api/search?limit=1000&text=consider

params:

* limit - number of results to return
* uri - url encoded uri to get annotations for
* user - get annotations for a particular user.
* quote - words that the annotation is quoting.
* text - search annotation text.

/annotations
============

Read
----

https://hypothes.is/api/annotations/<annotation id>

method: GET

get an annotation

Examples:

https://hypothes.is/api/annotations/utalbWjUQZK5ifydnohjmA

Create
------

https://hypothes.is/api/annotations/

method: POST

create a new annotation (needs authentication)

Update
------

method: PUT

update an existing annotation (needs authentication)

Delete
------

https://hypothes.is/api/annotations/<annotation id>

method: DELETE

delete an existing annotation (needs authentication)


.. toctree::
   :maxdepth: 1

   api/resources
