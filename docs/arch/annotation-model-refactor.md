## Current model

Annotation
    id - A UUID (uuid_generate_v1mc)
    document_id - FK to document
    userid - blah@hypothes.is
    authority - Available as a split on userid
    groupid - The pubid of the group
    created
    updated
    shared - boolean
    deleted - boolean
    text
    text_rendered
    target_selectors - jsonb
    extra - jsonb
    target_uri
    target_uri_normalized
    tags - List of text
    references - List of uuids

Annotation moderation

    id - Auto inc
    annotation_id - FK to annotation to UUID
    created
    updated

# Sorting the data

## Primary keys

    id - This should be a conventional int
    uuid - The original id
    group_id - FK to the group
    document_id - FK to the document
    user_id - FK to the user table
    authority_id - FK to a new authority table

## Primary meta

    created
    updated
    shared
    deleted

## Retrieval focused big chunks

    text
    text_rendered
    target_selectors - jsonb
    extra - jsonb

## Cross references

    tags - List of text

## WTF?

    target_uri
    target_uri_normalized

Why do we have these at all? We link to the document which has `web_uri`. I
don't get it, but they aren't always the same?

    references - List of uuids

We use the first item (the root) and the last (the parent), but do we use the
intermediate values?

# Ideas

## `Authority`

    id - Auto inc
    authority - String of the authority

## `Annotation`

    id - This should be a conventional int
    uuid - The original id 
    group_id - FK to the group table
    document_id - FK to the document table
    user_id - FK to the user table
    authority_id - FK to the authority table
    created
    updated
    shared
    deleted

## `AnnotationData`

    id - 1:1 link to Annotation id
    extra - jsonb
    text - Text entered by user, potentially markdown
    text_rendered - Rendered after being run through markdown rendering
    target_selectors - jsonb
    target_uri - ??? Can we kill?
    target_uri_normalized - ??? Can we kill?

## `Tags`

    id
    text

## `AnnotationTag`

    annotation_id
    tag_id

## `AnnotationRelation` ???

Parent and child would be nice on the annotation, and we could generate this
from it?

    parent_id
    child_id
    relationship_type - Enum (root, ancestor, parent)?
