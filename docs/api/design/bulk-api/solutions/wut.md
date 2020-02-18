# User-Group membership

## Overview

The user group membership is the only sticky item to design, as it doesn't 
exist as a primary object in it's own right.

The question here is how do we represent this relationship?

## Existing representation

URL only

    /groups/2348973b498e3d4/members/acct:my_username@some_authority
    
    
    
    
## Suggestions

There's no real prior art I can see for directly referencing one object from
another in our API. A couple of suggestions leap out:

    # id suffix to id string
    {
        "userid": "acct:my_username@some_authority",
        "groupid": "2348973b498e3d4"
    }

    # {item} to id string
    {
        "user": "acct:my_username@some_authority",
        "group": "2348973b498e3d4"
    }
 
    # {item} to object
    {
        "user": {"id": "acct:my_username@some_authority"},
        "group": {"id": 2348973b498e3d4"}
    }
    
    # Bear in mind we will often be using references like this:
    {
        "user": {"$ref": "#user_2"},
        "group": {"$ref": #group_31"}
    }
    
    
Of these I think the first is the worse. It somewhat matches our current API
in places, but not in a good way. The `groupid` of a group is not it's id. It
also doesn't follow the rest of the API which is snake case.

The second is the simplest, we can kind of assume that if we have a single 
string that it's the id.

The last one is a bit more verbose but has some advantages:
 
 * The item is a `user` or `group` just a very degenerate version
 * It's very easy to embed the objects with a `GET` request without requiring 
 the caller to change their code. You just fill out the rest of the fields.
