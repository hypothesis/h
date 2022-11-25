DROP MATERIALIZED VIEW IF EXISTS report.annotation_user_counts CASCADE;

CREATE MATERIALIZED VIEW report.annotation_user_counts AS (
    SELECT
        -- Cast to a date as it's 4 bytes instead of 8
        DATE_TRUNC('week', created)::date AS created_week,
        authority_id,
        user_id,
        COUNT(1)::integer AS count
    FROM report.annotations
    GROUP BY created_week, authority_id, user_id
    ORDER BY created_week, authority_id, user_id
) WITH NO DATA;
