DROP MATERIALIZED VIEW IF EXISTS report.annotation_group_counts CASCADE;

CREATE MATERIALIZED VIEW report.annotation_group_counts AS (
    SELECT
        -- Cast to a date as it's 4 bytes instead of 8
        DATE_TRUNC('week', created)::date AS created_week,
        authority_id,
        group_id,
        COUNT(1)::INTEGER AS count,
        (COUNT(1) FILTER (WHERE shared IS TRUE))::INTEGER AS shared,
        (COUNT(1) FILTER (WHERE ARRAY_LENGTH(parent_uuids, 1) > 0))::INTEGER AS replies
    FROM report.annotations
    GROUP BY created_week, authority_id, group_id
    ORDER BY created_week, authority_id, group_id
) WITH NO DATA;
