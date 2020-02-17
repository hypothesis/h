## Example

_Spaces added for clarity. Exact contents not yet decided._

    POST /bulk
    Accept: application/vnd.hypothesis.v1+x-ndjson
    Content-Type: application/vnd.hypothesis.v1+x-ndjson
    Content-Length: 97800
    
    ["job", "config", {"view": <response type>, "default": {"*": {"create": {"on_duplicate": "continue"}}}]
    ["user", "upsert", {... upsert content ...}, {"$id": "#user_0"}]
    ["group", "upsert", {... upsert content ...}, {"$id": "#group_0"}]
    ["group", "upsert", {... upsert content ...}, {"$id": "#group_1"}]
    ["group", "upsert", {... upsert content ...}, {"$id": "#group_2"}]
    ["group_membership", "create", {"user": {"$ref": "#user_0"}, "group": {"$ref": #group_0"}}]
    ["group_membership", "create", {"user": {"$ref": "#user_0"}, "group": {"$ref": #group_1"}}]
    ["group_membership", "create", {"user": {"$ref": "#user_0"}, "group": {"$ref": #group_2"}}]
    
Response with `view: null`

    HTTP/1.1 204 OK
    
Response with `view: "json_api"` or unspecified (default)

    HTTP/1.1 200 OK
    Content-Type: application/vnd.hypothesis.v1+x-ndjson
    Content-Length: 73660
    
    {"data": {"type": "user", "meta": {"$id": "#user_0"}, "id": "<user id>",  "attributes": { ... user data ...}}
    {"data": {"type": "group", "meta": {"$id": "#group_0"}, "id": "<group id>",  "attributes": { ... group data ...}}
    {"data": {"type": "group", "meta": {"$id": "#group_1"}, "id": "<group id>",  "attributes": { ... group data ...}}
    {"data": {"type": "group", "meta": {"$id": "#group_2"}, "id": "<group id>",  "attributes": { ... group data ...}}
    {"data": {"type": "group_membership", "id": "<membership id>", "attributes": { .. membership data ...}}
    {"data": {"type": "group_membership", "id": "<membership id>", "attributes": { .. membership data ...}}


## Outline

### End-point

    POST /bulk
    Accept: application/vnd.hypothesis.v1+x-ndjson
    Content-Type: application/vnd.hypothesis.v1+x-ndjson
    Content-Length: <length in bytes>
    
    [ ... global job configuration ... ] (optional)
    [ ... instruction 1 ... ]
    [ ... instruction 2 ... ]
    [ ... inline job re-configuration ... ] (optional)
    [ ... instruction 3 ... ]

### Job configuration
    
    [ "job", "config", <config> ]

Where `config` is a dict like:

```javascript
{
    // Don't send any return body
    "response": null,
    
    // Modify processing and error handling (future)
    "on_error": "continue",
    "async_processing": "auto",
    
    // Allow async calling (future)
    "async": true,
    "name": "User job name",
    
    // Provide defaults for certain actions (future)
    "default": {
        "*" : {
            "*": {
                ... defaults for all actions ...
            },
            "upsert": {
                ... defaults for all upsert actions ...
            }
        },
        "user": {
            "*": {
                ... defaults for all user actions ...
            },
            "upsert": {
                ... user upsert specific defaults ...
            }
        }
    }
}
```

_Note: There is no plan to implement 90% of the above, but if we did, this is where it would go._

### Individual instructions

    [ <object_type>, <action>, <body>(, <config>)? ]

Where:

 * `object_type` is one of  `["user", "group", "group_membership"]`
 * `action` is one of `["upsert", "create"]`
 * `body` is `action` and `object_type` specific
 

