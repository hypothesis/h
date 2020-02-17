# How to

* [Overview](#overview)
* [Alternatives](#alternatives)
    * [Separate query and body, with merge option](#solution_1) ✔
    * [Separate query and body](#solution_2)
    * [Guess which fields to search on](#solution_3)
* [Conclusions](#conclusions)

# <a name='overview'></a>Overview

To process potential creates/updates depending on current DB state we will 
need an upsert style behavior to prevent us from having to write any kind of
'if this then that' style behavior into our API.

But how should that be represented?

## See also

* [MongoDB Upserts](../research/mongo-upserts.md) - Research into how Mongo DB handles very similar issues

# <a name='alternatives'></a>Alternatives

_The names and fields specified here are for discussion only, not the final thing._

## <a name='solution_1'></a>Separate query and body, with merge option (✔️)

    [
        "user", "upsert",
        {
            "query": {
                "email": "user@example.com"
            }, 
            "update": {
                "name": "New name here",
            }
        },
        {"merge_query": true}
    ]

Nice:

 * Schema can allow and disallow fields for searching separately
 * Allows specific control of what is being searched on
 * Allows the query and update to be different
 * Doesn't duplicate fields unnecessarily
 * Merge option can be set globally, removing repetition* Can accommodate more complicated patterns (like multiple updates, or complete replacements)
 * Allows generic behavior for querying rather than object specific
 
Not so nice:

 * Bloats call with `query` and `update` fields or similar wrappings
 * If we aren't careful, we might allow more power than we intend

## <a name='solution_2'></a>Separate query and body (❌)

    [
        "user", "upsert",
        {
            "query": {
                "email": "user@example.com"
            }, 
            "update": {
                "email": "user@example.com",
                "name": "New name here",
            }
        }
    ]


Nice:

 * Most of the benefits of "Separate query and body, with merge option" above
 * Most explicit about behavior   
   
Not so nice:

 * Most of downsides of "Separate query and body, with merge option" above
 * Duplicate fields unnecessarily
  
## <a name='solution_3'></a>Guess which fields to search on (❌)

    [
        "user", "upsert",
        {
            "email": "user@example.com",
            "name": "New name here",
        }
    ]
Nice:

 * Most compact
 * Caller can't search for anything we don't explictly want them to
 
Not so nice:

 * Nasty implicit behavior defined on server side
 * Can't search for fields different to what we set
 * Can't easily express in a schema which fields are which
 * Can't accommodate more complicated patterns (like multiple updates, or complete replacements)
 * Binds our hands in the future
 
# <a name='conclusions'></a>Conclusions

### We will bind our hands forever if we don't separate query and update

If we have a single object we will have a single way of updating that object 
unless we implement:

 * A million flags to change how it works (`"user_upsert_style": "name_and_email_only"`)
 * New replacement upsert: `["user", "upsert_by_flexible_now", ...]`
 
All of these would be ugly and restrictive. By choosing to separate now we can
allow richer behavior in future, even if we don't need it right now.

### Separate values allow much more advanced behavior

___We don't need any of this right now___, but it would be very easy to do things 
like:

Set different things depending on whether this is an update or not:

    ["user", "upsert", {
        "query": {
            "email": "old@example.com",
        }
        "update": {
            "name": "Some new name",
            "email": "old@example.com",
        },
        "on_update": {
            "confirmed": true,
        },
        "on_insert": {
            "confirmed": false,
        }
    }]

Update multiple things:

    [
        "user", "update", 
        {
            "query": {
                "setting": "old_value",
            }
            "update": {
               "setting": "new_value",
            }
        }, 
        {"insert_multiple": True}
    ]

### There are lots of different ways to represent this

Assuming we are going to have separate queries and such then there are a lot of
choices left to be made about how to represent this.

One possible source of inspiration is Mongo DB which deal with similar problems (JSON updates and upserts of objects):
* [MongoDB's bulk upsert methods](https://docs.mongodb.com/manual/reference/method/Bulk.find.upsert/)
* [findAnyModify()](https://docs.mongodb.com/manual/reference/command/findAndModify/#dbcmd.findAndModify)
* [Upsert behavior](https://docs.mongodb.com/manual/reference/method/db.collection.update/#upsert-behavior)

This includes a bunch of rules/operations/syntax inspiration we might not think
 of such as having a single body which mutates how it behaves with special key.

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