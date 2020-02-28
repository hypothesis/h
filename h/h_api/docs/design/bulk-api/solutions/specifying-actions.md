# How to specify individual actions

* [Overview](#overview)
* [Alternatives](#alternatives)
   * [List wrapper](#solution_1) ✔
   * [Variable keys in dict](#solution_2)
   * [Static keys in dict](#solution_3)
* [Conclusions](#conclusions)

# <a name='overview'></a>Overview

# <a name='alternatives'></a>Alternatives

## <a name='solution_1'>List wrapper (✔️)
 
    [
        "user", 
        "create", 
        { ... payload ... }, 
        { 
            "<extra_option_1>": ...,
            "<extra_option_2>": ...
        }
    ]

Nice:

 * Reads well
 * Most compact
 * Always clear with NDJSON
 
Not so nice:

 * Optional last argument is a little annoying 
 
__HOT OFF THE PRESS!__

If we end-up using JSON API, we don't need the final extra options, as they
can be acommodatated in the payload in the `meta` variable.

We also don't need the object type up-front meaning it would look more like this

    ["create", {"data": {"type": "user", ...}]
    
This loses much of the readability of the list structure, but unifies input and
output.

## <a name='solution_2'>Variable keys in dict (❌)

    {
        "user": {
            "create": {... payload ...},
            "<extra_option_1>": ...,
            "<extra_option_2>": ...
        }
    }

Nice:

 * Quite compact
 * Reads well
 
Not so nice:

 * Variable keys are a pain in schema
 * Variable keys are a pain to code for
 * Extra options are kind of shoe horned in (no obvious home)
 * Without nesting in the extra options key ordering can result in hard to read NDJSON
 
## <a name='solution_3'>Static keys in dict (❌)

    {
        "item": "user",
        "action": "create",
        "data": {... payload ...},
        
        "<extra_option_1>": ...,
        "<extra_option_2>": ...
    }
    
Nice:

 * Static keyed items are easy to write schema for
 * Easy to program
 
Not-so-nice:

 * Most verbose
 * Doesn't read very nicely
 * Variable key ordering could result in un-readable NDJSON
  
## Extra options separate from actions (?)

If we have a series of atomic actions, we could separate out any additional 
processing instructions into a separate configuation item which applies until
another configuration item is found:

Instead of:

    ["user", "insert", {... payload ...}, {"on_error": "continue"}]
    ["user", "create", {... payload ...}, {"on_error": "continue"}]
    
We could have:

    ["_job", {"on_error": "continue"}]
    ["user", "insert", {... payload ...}]
    ["user", "create", {... payload ...}]
    
Nice:

 * With many actions sharing the same options this is more compact
 * Separates processing instructions from payload (our code is likely to mirror this approach)
 * Removes readability problems from the dict key approach (as the keys are now always ordered)

Not so nice:

 * With many actions with different options this is less compact
 * Actions are now contextual and must be processed in order (this was probably
   true anyhow)

# <a name='conclusions'></a>Conclusions

_Warning: Some of this is out of date, if we use JSON-API objects!_

#### There is a clear readability gap (list > var dict > static dict)

For the sake argument we will imagine that keys are jiggled randomly in dicts
(as they could be) then the following three instruction sets are the same.

If we imagine each of the above solutions being used in an NDJSON context:

Static key:

    {"item": "user", "action": "create", "data": {... payload ...}, "on_error": "continue"}
    {"data": {... payload ...}, "item": "user", "action": "create", "on_error": "continue"}
    {"on_error": "continue", "item": "user", "action": "create", "data": {... payload ...}}
    {"action": "upsert", "data": {... payload ...}, "item": "user"}
    {"on_error": "continue", "action": "insert", "data": {... payload ...}, "item": "user"}
    {"action": "create", "on_error": "continue", "item": "user", "data": {... payload ...}}

Variable key:    
    
    {"user": {"create": {... payload ...}, "on_error": "continue"}}
    {"user": {"on_error": "continue", "create": {... payload ...}}}
    {"user": {"create": {... payload ...}, "on_error": "continue"}}
    {"user": {"upsert": {... payload ...}}}
    {"user": {"insert": {... payload ...}, "on_error": "continue"}}
    {"user": {"on_error": "continue", "create": {... payload ...}}}
    
List:

    ["user", "create", {... payload ...}, {"on_error": "continue"}]
    ["user", "create", {... payload ...}, {"on_error": "continue"}]
    ["user", "create", {... payload ...}, {"on_error": "continue"}]
    ["user", "upsert", {... payload ...}]
    ["user", "insert", {... payload ...}, {"on_error": "continue"}]
    ["user", "create", {... payload ...}, {"on_error": "continue"}]
    
The list is clearly easier to read.

#### Using separate job instructions removes the readability gap with variable dicts and lists

Variable key: 

    {"_job": {"on_error": "continue"}}
    {"user": {"create": {... payload ...}}
    {"user": {"create": {... payload ...}}
    {"user": {"create": {... payload ...}}
    {"_job": {"on_error": "fail"}}
    {"user": {"upsert": {... payload ...}}}
    {"_job": {"on_error": "continue"}}
    {"user": {"insert": {... payload ...}}}
    {"user": {"create": {... payload ...}}}
    
List:

    ["_job", {"on_error": "continue"}
    ["user", "create", {... payload ...}]
    ["user", "create", {... payload ...}]
    ["user", "create", {... payload ...}]
    ["_job", {"on_error": "fail"}
    ["user", "upsert", {... payload ...}]
    ["_job", {"on_error": "continue"}
    ["user", "insert", {... payload ...}]
    ["user", "create", {... payload ...}]

#### Separate options outside of actions are maybe a separate concern

Specifying extra processing options is different from the main structure and
can be considered separately. It's nice in some ways and interacts with this
decision, but is covered in more detail here:
    
#### Using lists seems to have the most upsides right now

The list is:

 * Most compact
 * Always readable
 * Does not require separate job instructions to be readable (meaning we can delay thinking about them)
 
