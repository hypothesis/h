WITH
    last_update_date AS (
        SELECT MAX(last_update) FROM (
            -- We remove a time segment here to ensure an overlap. If the date
            -- is accurate to a day, it should be a day, if it's accurate to
            -- the second, it can be a second
            SELECT MAX(updated) - INTERVAL '1 second' AS last_update FROM report.annotations
            UNION
            -- Looks like the table is empty... start from scratch. This
            -- shouldn't really happen, but this prevents us from crashing if
            -- it does
            SELECT NOW() - INTERVAL '100 year'
        ) AS data
    )

INSERT INTO report.annotations (
    uuid,
    user_id, group_id, document_id, authority_id,
    created, updated,
    deleted, shared, size,
    parent_uuids, tags
)
SELECT
    annotation.id as uuid,
    users.id as user_id,
    groups.id as group_id,
    document_id,
    authorities.id as authority_id,
    annotation.created::date,
    annotation.updated::date,
    deleted,
    shared,
    LENGTH(text) AS size,
    "references",
    tags
FROM annotation
JOIN "user" users ON
    users.authority = SPLIT_PART(annotation.userid, '@', 2)
    AND users.username =  SUBSTRING(SPLIT_PART(annotation.userid, '@', 1), 6)
JOIN "group" as groups ON
    groups.pubid = annotation.groupid
JOIN report.authorities ON
    authorities.authority = users.authority
WHERE
    annotation.updated >= (SELECT * FROM last_update_date)
-- Ensure our data is in created order for nice correlation
ORDER BY annotation.created
-- None of the fields in this table change over time
ON CONFLICT (uuid) DO UPDATE SET
    updated=EXCLUDED.updated,
    group_id=EXCLUDED.group_id,
    deleted=EXCLUDED.deleted,
    shared=EXCLUDED.shared,
    size=EXCLUDED.size,
    parent_uuids=EXCLUDED.parent_uuids,
    tags=EXCLUDED.tags;

-- Do we want to analyze every time we insert? This could take a while?
ANALYSE report.annotations;
