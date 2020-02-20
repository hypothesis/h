# How to

* [Overview](#overview)
* [Alternatives](#alternatives)
    * [Empty object with relationships](#solution_1) ✔
    * [Object with ids](#solution_2)
    * [Relationship on user or group ](#solution_3)
* [Conclusions](#conclusions)

# <a name='overview'></a>Overview


# <a name='alternatives'></a>Alternatives

I think we're settling on JSON-API style objects now, so this section doesn't
consider alternatives. All of these are some flavour of JSON-API.

This is the case where this kind of seems the biggest shame, as the object
will get so much bloat.

## <a name='solution_1'></a>Empty object with relationships (✔️)

    {
        "data": { 
            "type": "group_membership",
            "relationships": {
                "member": {"type": "user", "id": "acct:user@example.com"},
                "group": {"type": "group", "id": "group:name@example.com"},
            }
        }
    }

Nice:

 * Follows JSON-API
 * Semantically correct
 
Not so nice:

 * Verbose

## <a name='solution_2'></a>Object with ids (❌)

    {
        "data": { 
            "type": "group_membership",
            "attributes": {
                "member":  ...,
                "group": ...,
            }
        }
    }

Gonna keep this short. JSON API says don't embed your objects. Relationships
are there for this.
  
## <a name='solution_3'></a>Relationship on user or group (❌)

    {
        "data": {
            "type": "group",
            "relationship": {
                "member": {"type": "user", "id": "acct:user@example.com"}
            }
        }
    }
    
    ..or
    
    {
        "data": {
            "member": {"type": "user", "id": "acct:user@example.com"}
        }
    }

I'm going to cut this one short by saying, there's no nice way to actually do
this and honour the JSON-API semantics around updating a group.

If we pick the first, then this would replace a single member for the group.

If we pick the second we have the problem of specifying which group in the 
absense of a path.

# <a name='conclusions'></a>Conclusions

I don't think there's much of a contest, we should have a `group_membership`
object with relationships to a member and group.