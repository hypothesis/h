# Specification of processing behavior

* [Overview](#overview)
* [Alternatives](#alternatives)
    * [Additional inline job instructions](#solution_1) ✔️
    * [Inline parameters](#solution_2) ✔
    * [Query parameters](#solution_3)
    * [Entry in a wrapper JSON object](#solution_4)
    * [Additional headers](#solution_5)
    * [Path parameters](#solution_6)
    
* [Conclusions](#conclusions)

# <a name='overview'></a>Overview

It would be very nice to allow asynchronous processing to allow the following 
kinds of behavior:

 * Kick a job off and check back on it later
 * State that we don't want an answer (just get on with it)
 * State that some actions are allowed to fail etc.

# <a name='alternatives'></a>Alternatives

## <a name='solution_1'></a>Additional inline job instructions (✔️)

    {"job": {"async": true, "blind": true}}
    { ... payload 1 ... }
    { ... payload 2 ... }
    { ... payload 3 ... }
    
Nice:

 * Easy to emit and parse
 * JSON but NDJSON friendly
 * Supports arbitrarily large instructions should you need them
 * Is a decent solution to adding additional processing instructions to each
   argument
 * Potential to allow instructions at different parts of the stream
    * Could change the rules half way through
    * You could state things should be processed in parallel, and break them
      into chunks
    * You could queue _multiple_ async bulk queries and check back on them
    * Can't immediately think why you'd want this, but it's very fancy
    * This is all sounds very [YAGNI](https://en.wikipedia.org/wiki/You_aren%27t_gonna_need_it) to me 

Not so nice:

 * Mixes payload and metadata
 * Doesn't allow for item specific config (all options apply to all actions)

## <a name='solution_2'></a>Inline parameters (✔)

We could include instructions inside each payload

    {"user": {"create": { ... payload ... }, "async": true}}
    
Nice:

 * Good local instruction binding
 
Not so nice:

 * Doesn't really make sense for global options
 * Might lead to lots of repetition


## <a name='solution_3'></a>Query parameters (❌)

    /bulk?async=1&blind=1
    
Nice:

 * Every likes query parameters
 * Easy to send and construct
 * Easy to parse
 * Separates instructions from payload 
 * Supports a medium number of instructions

Not so nice:

 * Maybe a little semantically odd. Not convinced...

## <a name='solution_4'></a>Entry in a wrapper JSON object (❌)

If we use a dict wrapper for the payload then we can easily add extra keys.

    {
        <options>: ...
        "actions": []
    }

Nice:

 * Trival to implement and use
 * Easy to build a payload and send it
 * Supports arbitrarily large instructions should you need them
    
Not so nice: 

 * Doesn't allow specific options for specific actions
 * Mixes payload and metadata
 * As mentioned in [How to structure the large scale request](request-structure.md),
  this would preclude using NDJSON, the favoroured approach.

## <a name='solution_5'></a>Additional headers (❌)

    X-Processing: do-this, do-that
    Accept: application/x-async

Nice:

 * Semantically correct as they specify processing instructions
 * Separates instructions from payload

Not so nice:

 * Doesn't allow specific options for specific actions
 * Nobody likes headers
 * They are a pain to set in Javascript 
 * Have a tendency to get stripped by proxy servers etc,
 * If you don't want them to get stripped you end up abusing existing headers
 * Doesn't easily support a large number of instructions
 
## <a name='solution_6'></a>Path parameters (❌)

    /bulk
    /bulk/async
    /bulk/async/0/blind/1/
    
Nice:

 * Separates instructions from payload
 * Easy-ish to call
 
Not so nice:

 * Doesn't allow specific options for specific actions
 * Semantically weird - These aren't resources but options
 * Horrible if you have lots of different options
 * Routing is a nightmare 
 * Doesn't support a large number of instructions

# <a name='conclusions'></a>Conclusions

#### A number of solutions are easy to rule out

 * Headers - Too small, weird and hard to preserve and use
 * Path params - Too small, bad routing and semantics
 * Global JSON object - Rules out serial processing and NDJSON
 
#### Query params and separate inline instructions both seem reasonable for global params

In favour of __query parameters__:

 * Separates content and processing instructions
 * Provides all the space we are likely to need for instructions

In favour of __inline job instructions__: 

 * Mixes content and processing instructions
    * If you have the payload, you know what happened
    * Allows easy dumps and syncs from files
 * Only one thing to get right as a user (payload, not payload + params)
 * Can apply schema to the instructions
 * Allows arbitrarily large additional options
 * Allows fancy pants changes of operating instructions part way through a job

#### Only per action and inline instructions support local options

Everything else is global only

#### Is there a conflation of local and global options?
 
Some options seem to be:

 * Inherently global - process these in parallel
 * Inherably local - Email the user on creation (doesn't apply to groups)
 * Both - If this/these fail: skip
 
#### Inline job instructions seem to have the edge

It's a fine line between query params and honestly, some of the advantages of
the inline instructions seem like things we _may_ not need in future. 

But why rule it out?

#### No decision is needed now

We can check which things get us stuck and what we rule out, but it's probably
to early to make any decisions right now.