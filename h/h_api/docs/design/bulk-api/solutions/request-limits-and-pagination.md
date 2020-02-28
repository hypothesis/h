# How to handle large requests

* [Overview](#overview)
* [Alternatives](#alternatives)
    * [Size limits](#solution_1) ✔
    * [Content-Length checks](#solution_2)
    * [Custom Content-Lines header](#solution_3) ✔
    * [Pagination and async jobs](#solution_4)
    * [Sentinel to mark the end of the request](#solution_5)
* [Conclusions](#conclusions)

# <a name='overview'></a>Overview

If we have a bulk API, it's certain that people will try to send it absurdly
large requests.

# <a name='alternatives'></a>Alternatives

All of these solutions are mutually compatible.

## <a name='solution_1'></a>Size limits (✔️)

To get around having to think about large request problems we could limit the
number of instructions that can be included in a single request.

This limit could be quite high and still probably achieve everything we need
right now. Small scale experiments showed a payload with 10,000 items was around
19Mb. So if we could have a limit of 1,000 or 100 and the response size would
be totally manageable for now.

Nice:

 * Simple to implement
 * A big limit (1000) will be total overkill for all current use-cases (LMS)
   and also result in very manageable payload sizes (~1Mb?)
 * We are more likely to be limited by time than space anyway (nice?)
    * The request might take a long time to process
 
Not so nice:

 * What if you want more than this?
 * Just make multiple requests?

## <a name='solution_2'></a>Content-Length checks (?)

With large requests it's entirely possible for the request to be cut-off before
we have received all of it. 

In the case of a plain JSON payload we would fail because we would assume the 
sender had not sent valid JSON (rather than it was lost in transit). In the case
of NDJSON it's possible that a request could be truncated at the exact split
between two documents.

In this case checking the `Content-Length` header would allow us to notice it 
was missing

Nice:

 * HTTP standard
 * Content agnostic
 * Well defined behavior
 * Libraries might well do it for you (on both sides)
 * Allows you to tell callers to go away:
    * Up front if the declared size is enormous
    * Part way through if they are under-declaring content length (for DOS 
      attacks etc.)
 
Not so nice:

 * Sending `Content-Length` requires the sender to know up front
   * This makes trivial streaming difficult
   * They could 'run' the request twice, once to get the size, again to send it
 * Calculating the value requires finesse if you are streaming the data on the
   read side too
 * Callers frequently mess up calculations due do to various pitfalls:
   * Bytes vs. Unicode chars (it's bytes)
   * New lines in general (`\n` vs `\n\r` etc.)
   * Confusion about HTTP wrapping (whether to include bare lines before etc.)

## <a name='solution_3'></a>Custom Content-Lines header (✔️)

Similar to `Content-Length` we could declare a number of `Content-Lines` 
which would indicate the number of rows of NDJSON to expect.

A similar alternative would be to declare this value early in the body somehow,
for example as part of [processing instructions](specifying-processing-instructions.md).

Nice:

 * Semantically similar to `Content-Length`, with similar protection
 * Extremely easy to calculate for sender and consumer
 * Can be calculated without reifying the content (good for streaming)
 * Allows you to reject jobs with too many instructions (rather than just 
   one long one)

Not so nice:

 * Non-standard
 * Usual hoo-ha with intermediaries discarding headers
 * Doesn't protect against JSON compatible chunks missing from individual requests
 * Behavior slightly undefined if we get truncated during the last instruction

## <a name='solution_3'></a>Pagination and async jobs (?)

If we want to have a truly bulk API (for example capable of syncing 1M 
annotations), we are going to need some pretty strong magic to make that 
happen.

It's not clear this could be achieved sensibly without submitting a job, which
is stored, and then processes asynchronously.

This would be theoretically very useful, but is a lot of work, and we probably
don't need it right now.
 
Nice:

 * Theoretically allows unlimited request and response sizes
 * Clearly a benefit if you can pull it off
 
Not so nice:

 * Not clear how to do this without significant engineering
 * Total overkill for now
 * Not clear how to handle arbitrarily large jobs with references
 
## <a name='solution_4'></a>Sentinel to mark the end of the request (❌️)

We could accept some kinds of book-ends or a sentinel to tell us the request
is complete:

    {"job": {"name": my_job", ...}}
    ... stuff ...
    {"end": ["my_job"]}

Nice:

 * Quite easy for both sides to create / check
 
Not so nice:

 * Mixes processing instructions and content
    * Not a problem if you are already doing this as a part of 
    [handling processing instructions](specifying-processing-instructions.md)
 * Kind of ugly
 * Non-standard
 * Behavior slightly undefined if we get truncated _during_ the sentinel
 
# <a name='conclusions'></a>Conclusions

### Size limits are about performance and give us a lot

All of our practical issues with size limits are probably solved with a hard
cut off. This will solve our peformance issues and is definitely good enough
 for now.
 
### Content-Length checks and sentinels are about correctness

If we are modifying the database en-masse as a result of a bulk input, we
probably want to make sure that we doing the right thing.

Therefore it's not really acceptable for us to get mixed messages about what 
the caller is asking us to do. These may be low probability events, but both
give us good protection against:

 * Truncated calls
 * Parts of the body lost in transit
 
Both of these might be less likely with a single plain JSON body (as it would
likely be invalid), but it's conceivable that partial receipt of a JSON request
could miss packets from the middle of the request and still be valid.

### Transit errors are probably low risk events

If we are hitting time limits during implementation, this might be something 
we want to leave on the cutting room floor.

Probability alone will likely give us some decent protection against these 
events as for it to be an issue they need to:

 * Occur at all (this isn't going to be common)
 * Occur in such a way as to leave the JSON valid

### Given the above `Content-Lines` is easy and effective

`Content-Lines` would give us marginally less protection, but is dirt cheap
to implement and streaming friendly. 

Given the expected low probability of errors in general, the number that should
get past this would be very low.

### Pagination and async jobs are overkill for now

It's a good idea, and if we ever want to start shipping hundreds of megabytes
of data about, we'll need to think about something like this, but for now we 
don't need it.

We are more likely to want async for "fire and forget" or async processing
type of functionality first.