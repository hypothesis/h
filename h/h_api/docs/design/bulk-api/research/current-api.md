# Groups

## Group create
>>>
    POST/PATCH /groups/{id}

    {
        "name": "string", *req
        "description": "string",
        "groupid": "string"
    }
    
<<<

    {
        "id": "string",
        "groupid": "string",
        "name": "string",
        "links": {
            "html": "http://example.com"
        },
        "organization": "string",
        "public": true,
        "scopes": {
            "enforced": true,
            "uri_patterns": []
        },
        "scoped": true,
        "type": "private"
    }

## Add user to group
    {user} is acct<username>@<authority>
    
    POST /groups/{id}/members/{user}

    DELETE /groups/{id}/members/{user}


# Users
## Create user

    POST /users
    
    {
        "authority": "string", *
        "username": "string", *
        "email": "user@example.com", *
        "display_name": "string",
        "identities": [
            {
                "provider": "string",
                "provider_unique_id": "string"
            }
        ]
    }
<<<

    {
        "authority": "string",
        "username": "string",
        "userid": "string",
        "display_name": "string"
    }
    
? ADD `id:acct<username>@<authority>`

### Get user

    {user} is acct<username>@<authority>

    GET /users/{user}
    
    {
        "authority": "string",
        "username": "string",
        "email": "user@example.com",
        "display_name": "string",
        "identities": [
            {
                "provider": "string",
                "provider_unique_id": "string"
            }
        ],
        "userid": "string"
    }

### Update user

    {username} here isn't acct<username>@<authority>?

    PATCH /users/{username}
    
    {
        "email": "user@example.com",
        "display_name": "string"
    }

<<<

    {
        "authority": "string",
        "username": "string",
        "userid": "string",
        "display_name": "string"
    }
