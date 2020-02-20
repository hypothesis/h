## Example

_Spaces added for clarity. Exact contents not yet decided._

    POST /bulk
    Accept: application/vnd.hypothesis.v1+x-ndjson
    Content-Type: application/vnd.hypothesis.v1+x-ndjson
    
    ["configure", {... configuration content ...}]
    ["upsert", {... user upsert content ...}]
    ["upsert", {... group upsert content ...}]
    ["upsert", {... group upsert content ...}]
    ["upsert", {... group upsert content ...}]
    ["create", {... group membership content ...}]
    ["create", {... group membership content ...}]
    ["create", {... group membership content ...}]
        
Response with `view: null`

    HTTP/1.1 204 OK
    
Response with `view: "json_api"` or unspecified (default)

    HTTP/1.1 200 OK
    Content-Type: application/vnd.hypothesis.v1+x-ndjson
    Content-Length: 73660
    
    {"data": {"type": "user", "meta": {"$anchor": "user_0"}, "id": "<user id>",  "attributes": { ... user data ...}}
    {"data": {"type": "group", "meta": {"$anchor": "group_0"}, "id": "<group id>",  "attributes": { ... group data ...}}
    {"data": {"type": "group", "meta": {"$anchor": "group_1"}, "id": "<group id>",  "attributes": { ... group data ...}}
    {"data": {"type": "group", "meta": {"$anchor": "group_2"}, "id": "<group id>",  "attributes": { ... group data ...}}
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
    
    [ "configure", <config> ]

Where `config` is a dict like:

```json5
{
    "view": null,

    "user": {
        "effective": "acct:user@example.com"
    },

    "instructions": {
        "total": 11
    },

    "defaults": [
        ["create", "*", {"on_duplicate": "continue"}],
        ["upsert", "*", {"merge_query": true}]
    ],

    // Allow async calling (future)
    "async": true,
    "name": "User job name"
}
```

_Note: There is no plan to implement all of the above, but if we did, this is where it would go._

See:

  * [Example configuration](schema/bulk_api/examples/job_configuration.json)

### Individual instructions

    [  <action>, <json_api_body> ]

Where:

 * `action` is one of `["upsert", "create"]`
 * `json_api_body` is a JSON API payload
 
See:

 * [Example upsert user](schema/bulk_api/examples/upsert_user.json)
 * [Example upsert group](schema/bulk_api/examples/upsert_group.json)
 * [Example create group membership](schema/bulk_api/examples/create_group_membership.json)
