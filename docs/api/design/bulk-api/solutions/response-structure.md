# How to package returned items

* [Overview](#overview)
* [Alternatives](#alternatives)
    * [NDJSON return values](#solution_1) ✔️
    * [List wrapper](#solution_2)
    * [Object wrapper](#solution_3)
    * [JSON API style wrapped items](#solution_4) ✔️
    * [Raw items](#solution_5)
* [Conclusions](#conclusions)

# <a name='overview'></a>Overview

From [How to represent items](representing-items.md) the settled upon solution
was to, long story short, have JSON object as the return value. None of the
solutions presented have anything else.

There is a question of how we package the multiple items when returning them.

# <a name='alternatives'></a>Alternatives

Not all of these alternatives are strict alternatives to each other. Some can
be combined. The two questions at play here are:

 * How to return the larger structure
 * How to return each item


## <a name='solution_1'></a>NDJSON return values (✔️)

The currently solution for [How to structure the large scale request](request-structure.md)
is to use separate each requested item as a row in a NDJSON document. It seems
reasonable if we accept this that we should return like this for similar reasons:

    {"meta": "Some info about how this all went?", ...}
    { ... return value 1 ... }
    { ... return value 2 ... }
    { ... return value 3 ... }

Nice

 * The caller can process the response as a stream 

Not so nice:

 * More effort for the caller to process returned data
 * Any global metadata has to become a separate row in the data

## <a name='solution_2'></a>List wrapper (❌)

Wrap the response as a list (like NDJSON above) 

Nice

 * The caller can process it easily by just decoding the JSON

Not so nice:

 * Can't stream
 * Any global metadata has to become a separate row in the data

## <a name='solution_3'></a>Object wrapper (❌)

    {
        "meta": "Some info about how this all went?", ...
        "data": [
            { ... return value 1 ... },
            { ... return value 2 ... },
            { ... return value 3 ... }
        ]
    }

Nice

 * The caller can process it easily by just decoding the JSON
 * Global metadata is easily accommodated

Not so nice:

 * Can't stream

## <a name='solution_4'></a>JSON API style wrapped items (✔️)

We could follow the [JSON API](https://jsonapi.org/format/#document-top-level) 
way of formatting documents to give us extra space to add metadata and related
information.

    {
        "data": {
            "id": "acct:user@authority",
            "type": "user",
            "attributes": { ... a user ... },
            "meta": {
                "$id": "user_provided_id"
            }
        }
    }

Nice

 * Space for row level metadata
 * Natively supports type information
 * Is a predefined standard, so people can read about it without us having to
   document it
 * This solves the `id` problem for the user as the JSON API standard mandates
   it on the outer level
 * The JSON API spec shows how to respond with:
   * Either data, or errors, which we could do on a action by action level
   * Multiple items should we want to on a row
   * Include 

Not so nice:

 * More verbose
 * Unless we include the id redudantly we should snip it out of the body
    * This means the consumer might have to put it back in some cases, which
      might seem like a hastle
 * Makes the payload bigger (so limits the max size)


## <a name='solution_5'></a>Raw items (❌)

When returning items in the above structures, we could put them in raw

    {... a user ...}

Nice

 * Most simple
 * Most compact

Not so nice:

 * No space for row level metadata
 * Can't easily tell the consumer what type of object this is without
  introducing another field mixed into the data

 
# <a name='conclusions'></a>Conclusions

### Size differences are small

A small experiment was performed with simulated responses using:

* User group membership links
* A small group with minimal details
* A large group with many long fields and details

In each case the item was repeated 10,000 times. In the case of list and raw
NDJSON, extra `type` and `$id` fields were mixed into the data.

For the NDJSON + JSON API these fields were included in the wrapper and `id`
was removed from the payload.

| Packaging         | Payload      | Size       | Overhead 
|-------------------|--------------|------------|----------
| NDJSON raw        | Links        | 1,880,000  | 0.00%
|                   | Small groups | 4,620,000  | 0.00%
|                   | Large groups | 18,850,000 | 0.00%
| List              | Links        | 1,890,000  | 0.53%
|                   | Small groups | 4,630,000  | 0.22%
|                   | Large groups | 18,860,000 | 0.05%
| NDJSON + JSON API | Links        | 2,090,000  | 11.2%
|                   | Small groups | 5,020,000  | 8.66%
|                   | Large groups | 19,250,000 | 2.12%

In the worst case scenario, we add around 11.2% overhead for the JSON API 
packaging. This is significant, but not outrageous.

Obviously the more metadata we include, the bigger this will get, but assuming
the data we return would be included anyway, then most of the price for the
JSON API style has already been paid. Therefore _more metadata_ would actually
_reduce overhead_.

### Large responses are still quite compact

Even with 10,000 large groups, the worst size above was around 19Mb.

### Streaming is still good

Even with smallish payloads, it's still nice to keep the ability to stream
because it increases the size of payload we can reasonably respond with 
enormously. 

There is a price to be paid in speed. A quick test reading 10,000 large groups
100 times gave the following results:

 * Bare list: 10.7s
 * NDJSON: 14.3s
 
The overhead is significant in isolation, but even in the 'worse' case 
scenario we are talking about 70k records per second.

The question of who's memory we are saving is a little complicated:

 * The consumer always benefits
 * The producer could benefit for retrieve heavy requests
 * The producer likely could not benefit for write requests in transactions as
   we cannot guarantee that the response will work until the end
   
This suggests some potential performance enhancements, should the user be 
allowed to send processing instructions. For bulk retrieve, the user could 
mark the request as "get only":

 * We could then process each part in serial
 * We could then start responding as soon as we could with results
 * We would error on any portion of the request which is not a bare retrieve

### JSON API wrapped items solve some problems for us

JSON API style object's main benefits are that it separates the payload from
metadata about the payload. We could always mix this data into the object and
then ask the user to strip it back out again, but this is kind of horrible and
would likely lead to us being gunshy about doing it.

Therefore the JSON API style would solve a few problems for us whilst introducing
a few trade offs:

 * Allows the `data.attributes` to be an __exact copy__ of the data we 
   currently return in the outer API with no modifications (where such objects exist)
 * We can return metadata separately from the data in a clean way
 * Provides a neat home to say what we are returning, the id and a reference
 * A more flexible return structure prevents us from binding future hands:
    * We can return mixed error and success values
    * We can return multiple objects in one NDJSON row (for example in response to a search)