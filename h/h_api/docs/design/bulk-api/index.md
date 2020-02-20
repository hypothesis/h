# Bulk API design

# Overview

## See also

 * [Current API research](research/current-api.md) - Details of relevant parts of our existing V1 API
 * [Visual summary](summary.md) - A quick summary of decisions

# Features

## We need

* Specify item type, action, payload
* Support multiple actions
* Upsert everywhere
* We need to be able to associate return bodies with the original items
* Some limits or handling of pagination

## Nice to have

* Stream line by line without having to hold the full request in memory
* It might be nice to know if we updated or created something for upserts _(future)_
* Allow the caller to declare _(future)_:
  * They don't care about the answer (it can be processed at our leasure)
  * That particular things can be skipped on error (delete if there)
* Be able to request no content, specific fields or partial return content _(future)_
* New items can reference each other, even when they don't ids yet _(future)_
  * We'll get away with this for now, as we predict ids 
  * This is no good for anyone else

# Basic decisions

## Path /bulk

Why be fancy. This does the job.

## Method POST

We don't want people to have to change the method depending on the blend of 
actions they've taken. `POST` also advertises that it's not safe to resend the
same request: in the general case it won't be.

There are some decent reasons to rule out some other methods too:

 * `PUT` - Implies this is idempotent. It could be, but it probably isn't. Also 
   the semantics of PUT are that you are putting the resource at the URL. We
   aren't "PUT"-ing the "/bulk".
 * `GET` - This could be semantically correct if all actions are gets, but many
   clients refuse to send a body with a get
 * `PATCH` - Kind of right sometimes, but generally weird and some clients 
   can't emit PATCH verbs (Java, I'm looking at you)

## Mime type

The existing API uses:

    application/vnd.hypothesis.v1+json
    
If we stay with plain JSON responses, there is no reason to change this. If we
use NDJSON however this will become inaccurate. The NDJSON mime type is:

    application/x-ndjson
    
Meaning the the new type would likely become:

    application/vnd.hypothesis.v1+x-ndjson

# Problems and solutions

* [How to structure the large scale request](solutions/request-structure.md)
  * __New line delimited JSON (NDJSON) with atomic actions on new lines__
  * Supports streaming behavior
* [How to specify individual actions](solutions/specifying-actions.md)
  * __Lists with positional arguments__
  * Compact and readable
  * Doesn't preclude or require processing instructions 
* [How to represent items](solutions/representing-items.md)
  * __JSON API objects for each item__
  * __Exact existing contents for user and group__
  * Following old conventions where we can
  * Inventing new objects where we must
* [How to represent the group membership](solutions/representing-group-membership.md)
  * __Empty JSON API object with relationships__
* [How to package returned items](solutions/response-structure.md)
  * __NDJSON rows with [JSON API](https://jsonapi.org/format/#document-top-level) style return values in each__
  * Allows separation of metadata from data, and 100% compatibility with existing objects
  * Does not bind future implementers hands 
* [How to handle large requests](solutions/request-limits-and-pagination.md)
  * __Fixed request limit size__
  * __Custom Content-Lines declaration__
  * Protects against most current performance and correctness problems
* [How to specify upserts](solutions/specifying-upserts.md)
  * __JSON API object (unless we don't use it elsewhere)__
* Specifying partial return or specific fields _(future)_
  * __No response required can be declared as a processing instruction__
  * Specific fields aren't required now
* [How to reference items before we know the id](solutions/referencing-items.md)
  * __The caller assigns an `$anchor` and can refer to it with `{"$ref": "assigned_id"}`__
  * Follows JSON Schema `$anchor` and `$ref` semantics
* [Specification of processing behavior](solutions/specifying-processing-instructions.md) _(future)_
  * ___Currently undecided___
  * Possibly separate processing instructions in the stream
  * Possibly per item instructions
  * Probably a mix of both
  
  
# Changes to existing capabilities

## Add upsert

We need a new upsert ability under the hood.

Currently to effect an upsert our code has to:

 * Look up the item
 * Catch a lookup error and then:
     * Create it if there was an error
     * ... or update it if there wasn't
     
This is two calls and requires conditional behavior. This will be a nightmare 
for any simple serial series of bulk actions. We don't want to have to build
any conditional logic into our API.

## User id should be formatted and returned

The user object should return an id. 

Many calls require the caller to provide
a user id, but we never give them one. They are expected to concatentate

    acct:<username>@<authority>
    
This should be in the return data, then the consumer never needs to do this
work and our instructions come "use the user id" rather than "here is how to
build it".

We could then remove code in LMS that replicates this behavior.