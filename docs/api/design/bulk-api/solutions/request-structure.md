# How to structure the large scale request

* [Overview](#overview)
* [Alternatives](#alternatives)
    * [NDJSON](#solution_1) ✔️
    * [Outer list wrapper](#solution_2)
    * [Outer dict wrapper](#solution_3)
    * [Grouped items](#solution_4)
* [Conclusions](#conclusions)


# <a name='overview'></a>Overview

How will the overall request be structured? 

Things we'd like to be true:

 * We support specifying extra arguments
 * The payload is easy to read
 * We can stream the contents

# <a name='alternatives'></a>Alternatives

## <a name='solution_1'></a>NDJSON (✔️)

_Mime type: application/x-ndjson_

New line delimited JSON (https://github.com/ndjson/ndjson-spec) allows for 
streaming of JSON content. This is a good fit for processing a potentially 
large number of actions as each item can be deserialsed individually without
loading the whole request into memory.

    { ... payload 1 ....}
    { ... payload 2 ....}
    { ... payload 3 ....}
    ...
    
This requires each payload be self contained rather than say grouping all user,
or all create actions together. This might be a good constraint to have as it
nudges us towards a generally parallel and atomic structure.

Nice:

 * Compact
 * Memory friendly
 * Easy to see individual actions in payload
 * Atomic things are easy to process and document

Not so nice:

 * There may be advantages to grouping (mark a set of actions as parallelisable)
 * Requires a little more effort for producer and consumer than raw JSON
 * Introduces the possibility of truncation in transit being undetectable
    * This could happen if the transmission is truncated exactly between two docs
    * See [How to handle large requests](request-limits-and-pagination.md) for more details
 
## <a name='solution_2'></a>Outer list wrapper (❌)

Basically as NDJSON but in a list

    [
        { ... payload 1 ....},
        { ... payload 2 ....},
        { ... payload 3 ....},
        ...
    ]
    
Nice:

 * Pure JSON is super easy to produce and consume
 * Most of the benefits of the structural leanings NDJSON
 
Not so nice:

 * Requires you to load full payload into memory to process
 * Will probably be an unreadable mess as a payload
 * Doesn't really buy you anywhere to put extra arguments
 
## <a name='solution_3'></a>Outer dict wrapper (❌)

Some kind of super structure with elements inside. These elements could be
the atomic items in a list above, or something else

    {
        <other_instructions> 
        ...,
        "actions": [
            { ... payload 1 ....},
            { ... payload 2 ....},
            { ... payload 3 ....},
            ...
        ]
    }
    
Nice:

 * Gives a trivial home for specifications about how to handle the request

Not so nice:

 * Makes everything a bit more verbose
 * Same downsides as an outer list wrapper
 
## <a name='solution_4'></a>Grouped items (❌)

We could group items by type or action, or both

    {
        "user": {
            "upsert": [
                { ... data 1 ....},
                { ... data 2 ....},
                ...
            ]
        },
        "group": {
            "upsert": [
                ...
            ]
        }
    }


Nice:

 * Cuts down on repetition
 * Might allow you to group items you want inserted in parallel
 
Not so nice:

 * No way to atomically process this
 * No easy way to specify different options for different things
 * Can't really see why you'd do this
 * We can work out that things are ok to put in parallel ourselves, or with
   explicit instructions to do so. The consumer might not be able to make this
   choice.

# <a name='conclusions'></a>Conclusions

#### Outer list wrapper doesn't buy you much over a dict

Between an outer list wrapper and outer dict wrapper, both have many of the 
same up and downsides, with the difference that the outer list wrapper doesn't even
buy you an obvious spot for extra arguments.

For that reason I'd say outer list wrapper is out.

#### NDJSON is the only solution that allows streaming

With NDJSON we could feasably open a DB transaction and start effecting each
action as we parse it before reading more of the request.

This is a significant benefit and means our API would not be subject to any
practical upper limit for request size as long as each part in the chain streams
correctly.

The downsides (some extra effort to parse and format, no obvious spot for 
extra options) don't seem as significant as this advantage for a bulk API.