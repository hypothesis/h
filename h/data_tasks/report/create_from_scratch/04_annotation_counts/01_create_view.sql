DROP TYPE IF EXISTS report.annotation_sub_type CASCADE;

CREATE TYPE report.annotation_sub_type AS ENUM (
    -- This is not a good name for a sub-type of an annotation, we should
    -- change this
    'annotation',
    -- Other primary types of annotation
    'reply', 'highlight', 'page_note'
);

-- This is a summary table which re-interprets the annotations data in terms of
-- weekly counts split by a number of facets:
--
--  * Authority
--  * Group
--  * User
--  * Annotation sub-type
--  * Annotation shared status
--
-- This is intended to speed up a variety of summary queries over the table and
-- make queries about the sub-type easy.

DROP MATERIALIZED VIEW IF EXISTS report.annotation_counts CASCADE;

-- There are various indicators of different sub-types of annotation, only
-- certain combinations should happen together. This table shows all
-- combinations and how we will interpret them.

-- This table is in the same order as the CASE statement below.

-- |----------|--------------|-----------|------------|-----------|
-- | Is Root? | Is Anchored? | Has text? | Sub-Type   | Expected? |
-- |----------|--------------|-----------|------------|-----------|
-- | False    | True         | True      | Reply      | No!       |
-- | False    | True         | False     | Reply      | No!       |
-- | False    | False        | True      | Reply      | Yes       |
-- | False    | False        | False     | Reply      | No!       |
-- | True     | False        | True      | Page-note  | Yes       |
-- | True     | False        | False     | Page-note  | No!       |
-- | True     | True         | False     | Highlight  | Yes       |
-- | True     | True         | True      | Annotation | Yes       |
-- |----------|--------------|-----------|------------|-----------|

CREATE MATERIALIZED VIEW report.annotation_counts AS (
    SELECT
        authority_id,
        group_id,
        user_id,
        -- Cast to a date as it's 4 bytes instead of 8
        DATE_TRUNC('week', created)::DATE AS created_week,
        CASE
            WHEN ARRAY_LENGTH(parent_uuids, 1) IS NOT NULL
                THEN 'reply'::report.annotation_sub_type
            WHEN anchored = false
                THEN 'page_note'::report.annotation_sub_type
            WHEN size = 0
                THEN 'highlight'::report.annotation_sub_type
            ELSE 'annotation'::report.annotation_sub_type
        END AS sub_type,
        shared,
        COUNT(1) AS count
    FROM report.annotations
    GROUP BY created_week, authority_id, group_id, user_id, sub_type, shared
    ORDER BY created_week, authority_id, group_id, user_id, count DESC
) WITH NO DATA;
