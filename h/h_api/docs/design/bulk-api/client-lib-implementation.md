# Client library implementation

## Table of contents

- [Overview](#overview)
- [Terminology in this document](#terminology-in-this-document)
- [Motivation](#motivation)
  * [Conclusions drawn from the motivation](#conclusions-drawn-from-the-motivation)
- [Comparison with existing](#comparison-with-existing)
  * [Comparison with H server side](#comparison-with-h-server-side)
    + [The major differences from the current approach](#the-major-differences-from-the-current-approach)
    + [Much of this is the same](#much-of-this-is-the-same)
    + [What might a view look like?](#what-might-a-view-look-like-)
  * [Comparison with client](#comparison-with-client)
- [Implementation details](#implementation-details)
  * [Our models contain the data privately](#our-models-contain-the-data-privately)
    + [A short rant about why POJOs suck](#a-short-rant-about-why-pojos-suck)
    + [A POJO tries to _be_ the data, these models _have_ the data](#a-pojo-tries-to--be--the-data--these-models--have--the-data)
  * [How we apply our schema](#how-we-apply-our-schema)
    + [Applying a single schema up front isn't nice for consumers](#applying-a-single-schema-up-front-isn-t-nice-for-consumers)
    + [We apply our schema in two phases](#we-apply-our-schema-in-two-phases)
  * [How the Bulk API is structured](#how-the-bulk-api-is-structured)
  * [Overview of data flow:](#overview-of-data-flow-)
- [How upcoming PRs are broken down](#how-upcoming-prs-are-broken-down)

## Overview

This document describes the idea behind the client library being created to
implement the processing logic for receiving and making bulk API calls.

This discusses some terminology, implementation decisions and the reasons for
them.

## Terminology in this document

### `Bulk API`

When discussing the `Bulk API` here, we typically are descibing the set of classes
and collaborators currently residing in `h.h_api.bulk_api` rather than the 
HTTP interface in the abstract.

### `model`

In the context of the Bulk API when we refer to `models` we mean domain or 
object models rather than database models. The Bulk API has no database of it's
own and only advises actions on the database.

These classes represent the problem space in some way, rather than exact 
DB columns or JSON fields (although all of the above are often the same/similar).

### `service`

The term `service` here is defined in the negative, as _not_ being models, views,
strict validation or other specialised app layers. i.e. It's just code / code
that doesn't fit neatly into one of these definitions. 

Services here _may_ be Pyramid services, but also
are probably just plain Python classes that encapsulate some specific behavior.

When discussing the Bulk API as a "service" it's likely that the service is 
performing or wrapping some behavior you might associate from other specialised
layers (like validation or serialisation).

### `JSON API`

JSON API is a particular way of structuring JSON bodies for requests and 
responses in an API, rather than the generic term.

See: https://jsonapi.org/

JSON API bodies tend to look something like:

```json5
{
    "data": {
        "id": "my_id",
        "type": "my_type",
        "attributes": {
            // All the fields here...
        },
        "meta": {
            // Custom additions here...
        }             
    }   
}
```

## Motivation

 * The Bulk API end-point is significantly __more complex__ than individual end-points
 * We'd like the __freedom to expand__ it in future, without being locked in
 * We should be __free to change__ as we've probably made mistakes in the design
 * Calling the API should be as __easy for a Python consumer__ as possible
 * __Bulk actions are dangerous__ so this should be as fool proof as possible
 
### Conclusions drawn from the motivation

 * Any view implementing this will be very large if the problem isn't broken 
   down more than usual
 * Model classes which are re-used between client and server implementations:
   * Reduce the chance of divergence
   * Make implementation on both sides easier
   * Allow better separation of concerns (you can code for a generic `Command` 
     instead of specifics to do with users and groups etc.)
 * Strict checking is good, we should apply validation to model objects where we 
   can (client and server)
 * Once models and schema are shared between client and server, it make sense
   to share other items where we can to reduce duplication
 * This moves more logic into the library and out of the view, which makes the 
   view thinner
 * An object which works it's way through a list of commands, checking them for
   validity, works equally for processing a set of commands as it does for 
   generating them
   
# Comparison with existing

## Comparison with H server side

| Task | H API views | H-API lib + Bulk view |
|-------------------|------------|------------------|
| Authentication  | Standard Pyramid stuff | As existing
| Routing         | Standard Pyramid stuff | As existing
| Deserialisation | View decodes data from request | View decodes strings from request, Bulk API converts to data
| Validation method | Custom schema class + In python JSON schema | Custom validator class + JSON schema in files
| Validation application | In view | In Bulk API
| Business logic  | Custom in view / services | In Bulk API object
| DB update logic | Custom in view / services | Batches arranged by Bulk API, effected by view / service
| Logic errors | View raising and, catching and re-raising from different code | View catching and re-raising from Bulk API for structural errors
| DB errors | In view / services | As existing
| Formatting responses | Custom in view / error views | In Bulk API object / error views

### The major differences from the current approach 

If you view the Bulk API as essentially a grandiose service, them the main
differences are:

* We have a data model which is separate from the DB and the JSON (although aligned with both)
* The Bulk API is not a complete service
    * It will require a sub-service to effect changes in the DB
    * We already have services which call each other, so that's arguably not really a change 
    * The Bulk API might be a little unique in the fact it strictly delegates _all_ modifications to another service
* Stylistically the Bulk API makes more distinctions between roles and jobs for code
   * Our other services just tend to do everything in house
   * The Bulk API is formed of a number of close collaborators
* Previously views would instantiate schema objects and apply rules, 
  now this is all delegated to Bulk API (the view really is plumbing alone)
  * The same will be true for return values if I can get it to work 
* The Bulk API is completely framework agnostic
 
### Much of this is the same

* Everything up until you get inside the view and after you exit it is identical
* All database operations will be conducted with existing mechanisms
* JSON schema is the validation mechanism
* The majority of differences are additions, not replacements

### What might a view look like?

Here is some totally gross pseudo code:

```python
@pyramid_view_fun_here(blah="blah")
def bulk_api_view(request):
    bulk_api_executor = request.find_service("bulk_executor")

    # Alternatively the view could be an executor
    # ... bulk_api_executor = self
 
    output = StringIO('')

    try {
        # If we can get the body as a stream, that's better
        BulkAPI.from_string(
            request.body_string,    # Sub real property here
            executor=bulk_api_exectutor, 
            output=output
        )
    }
    except JSONAPIException as e:
        # Or maybe just catch this with an error view
        raise PyramidHTTPErrorOfSomeType(e.as_dict())

    return json_response(output, 200)
```

The executor would need to conform to the `Executor` interface and might look a bit like

```python
class BulkExecutor(Executor):
    def configure(self, config):
        self.effective_user = config.effective_user

    def execute_batch(self, command_type, data_type, default_config, batch):
        # default_config here is options like {"on_duplicate": "continue"}
        # batch is a list of `Commands`

        if data_type == DataType.USER and command_type == CommandType.UPSERT:
            return self._go_do_that_then(batch, default_config)
        # ...

    def get_items(self, data_type, ids, config):
        return self._form_return(self.db_models[data_type].get(ids))    
```

## Comparison with client

We don't really have a separate client, so the major difference is anything exists
to help you at all.

This isn't currently a full client implementation (because it doesn't need to
be right now), but this is where would would build around.

The differences from this approach and how you _might_ do something like this:

 * You are using the exact same models and classes as the server
    * They aren't inspired, or representing etc. they are the same
 * This allows the client to very fully understand if the server will accept the
   request as it's being sent
 * This allows tighter feedback loops in implementation and testing for the client
 * The current design is to fail fast:
    * As soon as any part of a command is detected to be invalid we stop
    * This is to the extent that the command body is validated separately from the command wrapper
    * This allows very localised messages about what is wrong
    * As soon as any limit is breached we stop
    * Some items (total command count) still require holistic checking
 * As long as we are our only customer, the _library is the API_, not the HTTP/JSON concretisation
    * If the client and server use the same version of the library they will be compatible
    * This allows us a great deal of scope to change the representation, as long as the model interface is consistent

# Implementation details

## Our models contain the data privately

A common pattern for model objects is for them to:
 
 * Have a 1:1 mapping between attributes and the data being represented
 * Have a complete list of attributes and accessors supported by the data structure
 * Be a 'plain old' representation of the object without methods
 * To be 'unopinionated' about the state and content of the data
  
In the Java world there are refered to as Plain Old Java Objects, or __POJOs__. 
 
We do not take this approach. Our objects:

 * Contain a private plain Python data structure
 * Have properties and methods mutate this inner data structure
 * Apply strict schema to this data on creation and on demand
 * Only give access as a last resort
 * Has methods for related logic attached to the model
 
### A short rant about why POJOs suck

We don't have models, so we don't have POJOs, but it's a common way to go and I
want to say why I think they're awful.

 * They don't manage state, and are therefore the anti-thesis of encapsulation
 * A POJO can be in any and all states possible as you've no idea who mutated it or how
 * As they make no attempt to manage state you:
    * At best, have a companion logic object that duplicates and follows them around
    * At worst, have logic distributed all over your app about mutating them
 * You spend a lot of time writing accessors you never actually access in your code
 * They couple your code completely to your chosen data structure
 * They are bad at simply transporting data
 
Most APIs tend not to actually change the data they handle very much. We often
just read one or two fields to decide where something should go, and then hoy it
in a database.

### A POJO tries to _be_ the data, these models _have_ the data

Our models wrap and represent the data, but don't attempt to be it. This is a 
small distinction, and in many cases there is some break down (the properties
can be pretty getter/settery).

But this has some distinct advantages:

 * JSON and plain Python data structures can be essentially transparent
 * We can use this to our advantage to allow trivial application of schema at any time
 * We can use methods which change the object in controlled, known ways, from a guaranteed starting point
 * If the schema checks asserts existence of something, we don't actually have to write any code for it unless we need it
    * For example the user and group `attributes` are never explicitly mentioned in the code
    * They are interacted with at a dict level
    * This is because the exact contents are irrelevant to us for this code
    * This means they could change radically and (aside from the tests) we'd only have to change the schema
 * We don't write scads of objects and accessors representing fields that exist, but we don't actually need to direct processing
 
Adhering to this strictly does have some slightly odd effects:

 * Where we want our model objects to return other model objects care is required
 * This can result in what appears to be duplicate object creation
 * Caching can help here
 * Looks a little funny sometimes 
 
## How we apply our schema

As our data stream is NDJSON, not JSON, we can't apply a schema to the whole 
request so we are therefore necessarily interpretting the input to some extent
before we apply JSON schema to it.

### Applying a single schema up front isn't nice for consumers

Originally I was applying a single schema that just asserted that the command
as a whole was correct. This is good and bad, and in the end I moved away from 
this.

The good:

 * Validation happens up front and center
 * There's a single schema that applies to everything
 
The bad:

 * `oneOf` blocks always generate hypercryptic errors for the user
   * This is because if you fail to be any one of these schema, we don't know which one you were trying to be
   * It's usually super obvious to people which one is intended, but JSON schema just doesn't work that way
   * This makes people mad
 * Our errors would always refer to the body as embedded in the command wrapper
   * This is weird and wrong from a JSON API point of view
   * If we ever decided to start returning the same replies for single modification end-points our paths would be different

This actually happens as models are created. This is nice for us as it means
we get hyper focussed messages about what was wrong. A mistake in a body field
will result in validation errors from the body object in question not some opaque
up-front layer.

### We apply our schema in two phases

 * At a command wrapper level
 * At a command body level
 
The outer level ensures the structure is good enough that we can determine
what kind of command it is, and that it is not obviously broken.

Once we know what type of command it is we then apply a situation specific
schema to that object.

This has some advantages:

 * We make a distinction between custom non JSON-API trappings that we have added and single value errors
 * Any errors we get tend to be much more field specific
 
## How the Bulk API is structured

All items are relative to the root of the class structure.

Major classes:

 * __Validation__ provided by:
   * `schema.Schema` - Provides convenient access to `schema.Validator` objects
   * `schema.Validator` - Wraps schema validation to generate `SchemaValidationErrors`
 * __Models__ in:
   * `model.base.Model` - Add `Validators` to data structures and provide interface
   * `model.json_api.*` - Provides abstract objects representing JSON API basics
   * `bulk_api.model.data_body.*` - Individual payloads like `UpsertUser` based on JSON API
   * `bulk_api.model.config_body.Configuration` - Configuration payload
   * `bulk_api.model.command.*` - Wrappers combining CommandTypes and payloads
 * Model adjacent __misc things__:
   * `enums.*` - Various enums like `DataType` and `CommandType`
   * `bulk_api.command_builder.CommandBuilder` - Creates `Command` objects from raw data or provided convenience methods
 * __Main loop__:
   * `bulk_api.bulk_job.BulkJob` - Entry point for main algorithm
   * `bulk_api.command_batch.CommandBatch` - Represents a group of commands and logic for when the group needs to be executed
   * `bulk_api.id_references.IdReferences` - Keeps tabs on user provided references, concrete ids and subbing one for the other
 * __Entry points__ into the main loop:
   * `bulk_api.executor.Executor` - Abstract classes responsible for making changes to DB and reporting back
   * `bulk_api.observer.Observer` - Classes which are 'informed' of commands (used for serialisation/debugging)
   * `bulk_api.entry_point.BulkAPI` - Convenience methods bringing together all of the above

## Overview of data flow:

This is largely the same for the client and the server:

 * `Commands` are created using the `CommandBuilder`
 * Each `Command` is sent to the `BulkJob` one by one
 * The `Obvserver` is informed about each command going through 
   * Opportunity to serialise here for client
   * Mostly just absolute gold dust for debugging
 * The `BulkJob` stores commands in a `CommandBatch` until the batch decides commands must be dealt with
   * This happens if the list gets too long, or we swap from one type of command to another
   * This then calls the `BulkJob` back to let it know, which in turn calls the `Executor`
 * The `Executor` would actually put things in the DB in response and report on created ids
 * The `BulkJob` uses the returned ids to de-reference any future objects using the `IdReferences`
 * At the end the `Executor` is asked to retrieve items if they are needed (`view != None`)
   * This part isn't done yet but we would probably call the `Observer` with the return bodies
   * This would form the reply stream (in the case of the server, disabled for client)
   
# How upcoming PRs are broken down

 1. Schema and validators
 1. Model classes for data bodies (`UpsertUser`, `UpsertGroup`, `CreateGroupMembership`)
 1. Model for configuration body
 1. Models for command wrappers (`UpsertCommand` etc.)
 1. Command builder (`CommandBuilder`)
 1. Command batches (`CommandBatch`)
 1. Id reference store and de-referencer (`IdReferences`)
 1. Bulk Job and collaborators (`BulkJob`, `Executor`, `Observer`)
 1. Convenience wrappers (`BulkAPI`)
