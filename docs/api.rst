Source Documentation
====================

Reference material for the public APIs exposed is available in this section. It
It is targeted at developers interested in integrating functionality from
Hypothes.is into their own Python applications.

===============
API Endpoints:
===============

**/search**

Search for annotations annotations

Examples:

https://api.hypothes.is/search?limit=1000&uri=http%3A%2F%2Fepubjs-reader.appspot.com%2F%2Fmoby-dick%2FOPS%2Fchapter_003.xhtml&user=acct:gluejar@hypothes.is

https://api.hypothes.is/search?limit=1000&user=acct:gluejar@hypothes.is

https://api.hypothes.is/search?limit=1000&quote=limber

https://api.hypothes.is/search?limit=1000&text=consider


params:
* limit - number of results to return
* uri - url encoded uri to get annotations for
* user - get annotations for a particular user. syntax: acct:<username>@<provider> . Until there are other annotation providers, the provider is "hypothes.is". 
quote - words that the annotation is quoting. This is very brittle - text is not completely indexed, is punctuation sensitive and appears to index single words only. change your search word to lower case.
* text - search annotation text. This is very brittle - text is not completely indexed, is punctuation sensitive and appears to index single words only. change your search word to lower case.

**/annotations**

https://api.hypothes.is/annotations/<annotation id>

method: GET

get an annotation
    
Examples:

https://api.hypothes.is/annotations/utalbWjUQZK5ifydnohjmA

method: POST

create a new annotation (needs authentication)

params: 

refresh - a boolean that forces a refresh

method: PUT

update an existing annotation (needs authentication)

params: 
* refresh - a boolean that forces a refresh

method: PUT
delete an existing annotation (needs authentication)


**/search_raw**

Advanced search API - direct access to ElasticSearch. Uses the same API as the ElasticSearch query endpoint.


Missing in API??
* search for users by email
* search for annotations by tags

.. toctree::
   :maxdepth: 1

   api/resources
