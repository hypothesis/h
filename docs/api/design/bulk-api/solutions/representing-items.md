# How to represent items

* [Overview](#overview)
* [Alternatives](#alternatives)
    * [Plain JSON objects](#solution_1) 
    * [JSON API style objects](#solution_2) ✔
    * [Keep the path + JSON objects](#solution_3) 
    * [HAL `_links` + JSON objects](#solution_34
* [Conclusions](#conclusions)

# <a name='overview'></a>Overview

Currently items are referenced with a combination of:

 * URL
 * Body
 
In our case, the URL portion isn't available. How should we represent items?

## Our ids are all over the shop

We aren't consistent about what ids we have which will make this a pain

Annotations:

    {"id": "The real id"}

Groups:

    {
        "id": "The read id",
        "groupid": "Something totally different"
    }

Users:

    {"userid": "The read id?"}

Observations:

 * `userid` and `groupid` are titularly redundant on user and group objects
 * Both are horrible because everything else is snake case
 * `groupid` is particularly bad because it _isn't_ the group id
 * `groupid` appears to be something like a 3rd party ref
 * Everything should have an `id`

## Our paths are all over the shop too

Our URLs don't really put the Unique in URL. You can often access the same object
with multiple different URLs.

The user for example can be retrieved with a mixture of items in the URL.

# <a name='alternatives'></a>Alternatives

## <a name='solution_1'></a>Plain JSON objects (❌️)

Fully encode all the relevant data into the object. Make objects with no body
explicit. 

Previously a group membership item was:

    /groups/group:my_group@some_authority/members/acct:my_username@some_authority

Now it might be:

    {
        "user: {"id": "acct:my_username@some_authority"},
        "group": {"id": "group:my_group@some_authority"} 
    }

Nice:

 * Easy to run a schema over
 * Everything can be normalised

Not so nice

 * Our conventions are a mess, which makes this difficult
 * Breaks with the previous API

Note: [How we package the response](response-structure.md) could solve some problems here
by using [JSON API](https://jsonapi.org/format/#document-top-level) style wrapper
which allows metadata to be separated from the payload.

## <a name='solution_2'></a>JSON API style objects (✔️)

    {
        "data": {
            "type": "group",
            "attributes": { ... group data here ... }
        }
    }

    {
        "data": {
            "type": "group_membership",
            "relationships": {
                "member": {"id": "acct:my_username@some_authority"},
                "group": {"id": "group:my_group@some_authority"}
            }
        }
    }

Turns out [we can probably do upserts quite nicely using JSON API](specifying-upserts.md).

Nice:

 * Easy to run a schema over
 * Everything can be normalised
 * Matches our output if we use JSON-API there
 * Provides a solution to our messy conventions by hiding them
 
Not so nice:

 * Most bloat
 * Doesn't match our output if we _don't use_ JSON-API there


## <a name='solution_3'></a>Keep the path + JSON objects (❌️)

We could represent items by explicitly keeping the path about:

    {
        "uri": "/groups/group:my_group@some_authority/members/acct:my_username@some_authority"
    }
    
    {
        "uri": "/users/acct:my_username@some_authority",
        "data": {... all the rest...}
    }
 
Nice:

 * Maps to the previous API
 
Not so nice:

 * Maps to the previous API - our API has multiple 'unique' resource identifiers 
   (URI) for the same objects. It's possible to get users in multiple ways
 * Constructing paths sucks, asking users to do it really sucks
 * A schema can't really inspect the contents easily (unless it becomes a 
   pile of regexes)
 
## <a name='solution_4'></a>HAL `_links` + JSON objects (❌️)

I put this here, because I'm sure there's something you could do with HAL here,
but a couple of things:

 * HAL is for returning things, not sending them
 * It's basically the solution above but ugly and confusing
 * Nobody uses HAL and there's no tooling or understanding about it
 * HAL is worse than not having anything most of the time for reasons I'm 
   happy to go into. But I basically think it's an un-advantage.

# <a name='conclusions'></a>Conclusions

#### Paths are awkward for everyone

A short one here. I can't see any pressing reason to keep the paths around.

The paths would be:

 * A nice bit of fan service for all the hard core H API v1 fans with tattoos 
   of our API docs etc. but otherwise...
 * Really unpleasant to construct and deconstruct
 * Not even uniquely identifying
 * Unnecessarily binds us (and vice versa) to the routing of unrelated routes

#### We made it harder for ourselves, but JSON is the way

Desite some awkwardness around existing standards (or lack of them) around 
object field names, this is the way to go.

This obviously doesn't cover exactly what they will look like, but the obvious
thing is to stick very close to the existing output unless forced not to.

#### JSON API all the time, everywhere

If we are using this style in our output then we should use it in our input
too. 

It also tidies away some inconsitencies with our naming.