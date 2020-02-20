# How to reference items before we know the id

* [Overview](#overview)
* [Alternatives](#alternatives)
    * [User supplied references with cheaty `$id` and `$ref`](#solution_1) ✔
    * [Generic user supplied references](#solution_2)
    * [Implicit ids](#solution_3)
    * [JSON references, pointers, links etc.](#solution_4)
    * [Using some known portion of the object for reference](#solution_5)
    * [Guessing the id the resource will get](#solution_6)
* [Conclusions](#conclusions)
* [How does this help with `GET` semantics?](#gets)

# <a name='overview'></a>Overview

There are two related problems here:

 * If we create two items and link them, how do we specify the ids for the 
   link if neither exists yet?
 * If we retrieve 8 items, how do we easily tie up the 8 responses to the 
   objects asked for?
 
We don't actually need an answer to the second part, as currently LMS doesn't 
actually care about the response and does not do bulk retrieve. But it seems
like a sensible thing to think about.

## It's not a problem if you actually know the id

If you definitely know the id of the thing you are trying to link to or lookup
then it's not such a big problem. 

This is likely in the case of a semantic `GET`. You probably know the id you're
after, so you can just order items by the id after to match them up.

It's also not a problem with concrete know ids during creates and updates. You 
can just put them in.

### Assume strings are ids, and objects are references

All of the following solutions therefore assume the following:

 * If you know the id, you will include it directly as a string
 * Anything else is some kind of reference to the object that must be looked up 

## References out of order or missing are the users fault

Assuming the user is assigning ids they may reference ids:

 * That don't exist
 * They haven't assigned yet
 
We could read the whole request in, collate all of the references and
check they all line up. We could even modify the order of the call to ensure
we will create them in a good order.

This sounds exhausting though, and would also prevent streaming processing.

A simpler approach is to:

 * Start a transaction
 * Process as we go, storing created or retrieved ids for objects
 * If at any point we find we reference something we haven't looked up yet:
   * Backout the transaction, fail

# <a name='alternatives'></a>Alternatives

## <a name='solution_1'></a>User supplied references with cheaty `$anchor` and `$ref` (✔️)
Taking a inspiration from [JSON schema $id and $ref](https://json-schema.org/understanding-json-schema/structuring.html#using-id-with-ref) 
we can slightly cheat by expanding the concept to cover multiple documents.

    ["user", "create", {"$anchor": "user_1", ... payload ...}]
    ["user", "create", {"$anchor": "user_2", ... payload ...}]
    ["group_membership", "create", {"group": ..., "user": {"$ref": "user_2"}}]

Alternatives:

 * `@id` and `@ref` - Prevents confusion with schema keywords, but potentially 
   introduces JSON-LD confusion in it's place.

Nice:

 * It's good and explicit with little scope for confusion
 * Very nearly actually a standard
 * Familiar in a good way to people who know JSON Schema (the semantics are right)

Not so nice:

 * Bloats the call a little
 * Still requires users to create and track ids
 * Kind of a more elaborate version of the user generated ids
 
___Note___ A new draft of the JSON schema is phasing out using `$id` as an 
anchor, so I've swapped this over to the new `$anchor`.

https://json-schema.org/draft/2019-09/json-schema-core.html#rfc.section.8.2.3

## <a name='solution_2'></a>Generic user supplied references (❌)

It's on the user to provide a temporary id that we can then leverage:

    ["user", "create", {"@ref": 0, ... payload ...}]
    ["user", "create", {"@ref": 1, ... payload ...}]
    ["group_membership", "create", {"group": ..., "user": {"@ref": 1}}]

The exact name could be many things. Some alternatives:

 * `id` - Guaranteed to clash with existing things
 * `@id` - Like JSON-LD, but not. Not going to clash, but is misleading if 
   someone is familar with JSON-LD.
 * `_ref` - Indicates it's not a normal field. Might clash.
 * `$ref` - Could be confused with JSON schema `$ref`

Nice:

 * It's good and explicit with little scope for confusion
 * The caller can use whatever reference is most appropriate and comprehendable
   to them as long as it is unique and stringfies nicely (no floats please)
   
Not so nice:

 * The user has to generate some kind of id for everything
 * Bloats the call a little

## <a name='solution_3'></a>Implicit ids (❌)

We could generate ids based on the nth time an object has been seen.

    ["user", "create", {... payload ...}]   # I'm user 0!
    ["user", "create", {... payload ...}]   # I'm user 1!
    ["group_membership", "create", {"group": ..., "user": {"@ref": "user/1"}}]
 
Some alternatives:

 * `{'@row': 1}` - The nth thing in general. Not so nice if we also have inline
   processing instructions
 
Nice:

 * The user doesn't have to generate lots of ids
 * Kind of readable: `"user/1"` gives you a good idea what you're talking about
 * Less call bloat
 
Not so nice:

 * User has to infer what the ids we allocate will be
 * If we change our minds about how these work, the client is broken

## <a name='solution_4'></a>JSON references, pointers, links etc. (❌)

I put this here because you might think about using standard `$ref` links, or
paths etc. but you really can't with NDJSON as the navigation is between 
separate documents provided in the payload, not a single one.

This would be easier if you had a single document, but it's still not very nice
and kind of analogous to the solution above.
 

## <a name='solution_5'></a>Using some known portion of the object for reference (❌)

    ["user", "create", {"name": "burt", ... payload ...}]
    ["user", "create", {"name": "sally", ... payload ...}]
    ["group_membership", "create", {"group": ..., "user": {"name": "sally"}}]
 
Nice:

 * Doesn't require any superfluous data just for matching

Not so nice:

 * Duplicates data in the payload
 * Requires a different solution for every object type
 * What can you use as a reference, what can't you? When you reference a user
   what field is it again? 

## <a name='solution_6'></a>Guessing the id the resource will get (❌)

Just no. 

This may be possible for users, but in general it's not. It also ties
the consumer to assumptions about what the service will do and prevents the 
service from changing.
 
# <a name='conclusions'></a>Conclusions

#### Things which require the user to guess our behavior are bad

Both id guessing and implicit ids generated by the system require the user to
have a concept of how we will behave, without direct evidence. If their belief
is wrong, or out of date, the interface breaks.

For this reason the following solutions are probably out:

 * Implicit ids
 * Guessing the id the resource will get
 
#### Path based JSON pointers make no sense with NDJSON

Relative navigation in the document doesn't make sense across mulitple documents
so therefore this is out.

#### Referencing parts of objects sounds like work

We could technically use some of the parts we already know, but it sounds like
a lot of work to index objects by field or anything generic.

Ids are explicit and easy to code.

#### JSON style $anchor and $ref are explicit and familiar

But user supplied generic ids and anchor style ids are very similar solutions.

I would suggest the edge goes to using `$id` and `$ref` as it's not something
I invented. I would suggest we make the following exceptions:

 * We should document it as if only '#id' works
 * We should actually any old unique string to work
 
# <a name='gets'></a>How does this help with `GET` semantics?

We covered links in more detail, as they are the focus, but we can easily adapt
any id assigning method with the following rules:

 * If you assign a linking id, we'll echo it back to you in the returned object
 * If you don't send a linking id, you'll have to figure it out yourself
 
You send:

    ["user", "create", {"$anchor": "user_1", ...}]
    ["user", "create", {"$anchor": "user_2", ...}]
    
We reply:

    {"$anchor": "user_1", ...}
    {"$anchor": "user_2", ...}
    
Note: As mentioned in [How to package the response](response-structure.md), we 
may use JSON API style return values, which allow a `meta` field which would be
a natural home for this.