# Mongo upserts

## Overview

One possible source of inspiration for how we might format upserts is Mongo DB 
which deals with similar problems (JSON updates and upserts of objects):

* [MongoDB's bulk upsert methods](https://docs.mongodb.com/manual/reference/method/Bulk.find.upsert/)
* [findAnyModify()](https://docs.mongodb.com/manual/reference/command/findAndModify/#dbcmd.findAndModify)
* [Upsert behavior](https://docs.mongodb.com/manual/reference/method/db.collection.update/#upsert-behavior)

This includes a bunch of rules/operations/syntax inspiration we might not think
 of such as having a single body which mutates how it behaves with special key.

## Example syntax

As a quicky, for a replacement of the full document the Mongo equivalent would be:

    {
        findAndModify: "collection-name",
        query: {
            "email": "old@example.com"
        },
        update: {
            "name": "Some new name",
            "email": "old@example.com",
            ... every other fields or they disappear ...
        },
        "upsert": true
    }
 
Whereas to copy all existing contents (more like what we want)
  
    {
    findAndModify: "collection-name",
        query: {
            "email": "old@example.com"
        },
        update: {
            $set: {
                "name": "Some new name",
            }
        }
    }
    
## What we could learn from this

### Having a single body which is mutated by update operators

Mongo specifies a number of [update operators](https://docs.mongodb.com/manual/reference/operator/update/#id1) which
you can set in the body for a replacement. 

You either give a normal dict, or a dict with those values as keys. If none 
are present, then a direct replacement is performed.

This is interesting because rich behavior is permitted with a single field, 
allowing that to be expressed positionally.

We aren't bound by this, but it's interesting. For my taste it introduces 
confusion about whether you are looking at data or metadata. We might profit 
from avoiding this.

### There aren't many operators required for a full set of behaviors

Of particular interest to us here are probably:

 * `$set` - Take the existing document and add these fields
 * `$setOnInsert` - Sets the value of a field if an update results in an insert of a document. Has no effect on update operations that modify existing documents
 * `$unset` - Removes the specified field from a document

Most behaviors you might care to do is accommodated by this short list of 
modifiers.

### We could steal some names / concepts

An 'upsert' is considered a sub-set of an 'update' and is always in an 'update'
context. This is probably a biggy! Don't design this twice if we think we will want a non-upserting update one day.

 * 'query' - How we find what should be updated
 * 'update' - A conflation of instructions to update / the data to be updated
 * 'upsert' - Should we create if we don't find?
 * 'set' - Take a document, then set these specific fields
 * 'unset' - Take a document, then remove these specific fields
 * 'setOnInsert' - As above, but only on upserts
 * 'replaceWith' - Just replace the whole thing with this
 
There are some things which appear missing here conceptually:

 * 'unset_on_insert' makes no sense
 * 'set_on_update' actually does make sense, and is missing from Mongo.
   Whether anyone would actually need it is a different thing.

----

## Adapting to our context

    {
        // Query is a good name for how we find things
        "query": {... blah ...},
        
        // "replaceWith" could just be "replace"
        "replace": { ... just do this ...}
        
        // "set" seems decent and is nice and short
        "set": { ... take what's there but add these ... }
        
        // Again, "setOnInsert" is an ok name snakified 
        "set_on_insert": { ... add some more if it was a create... }
    }

For our purposes I'd say:

 * The whole single item with sometimes nested key words brings a
  data/instruction confusion we can do without
 * `query` and `set` (semantics and all) are pretty good first attempts
 * `set_on_insert` and `replace` aren't really needed yet
