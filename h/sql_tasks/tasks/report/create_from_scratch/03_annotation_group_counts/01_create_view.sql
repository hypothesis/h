DROP MATERIALIZED VIEW IF EXISTS report.annotation_group_counts CASCADE;

CREATE MATERIALIZED VIEW report.annotation_group_counts AS (
    SELECT
        data.*,
        EXTRACT('year' FROM created_week - INTERVAL '6 month')::smallint AS academic_year,
        CONCAT(
            EXTRACT('year' FROM created_week - INTERVAL '6 month'),
            '-',
            CASE WHEN EXTRACT('quarter' FROM created_week - INTERVAL '6 month') < 3 THEN 1 ELSE 2 END
        ) AS academic_half_year,
        COUNT(1)::integer AS count
    FROM (
        SELECT
            -- Cast to a date as it's 4 bytes instead of 8
            DATE_TRUNC('week', created)::date AS created_week,
            authority_id,
            group_id
        FROM report.annotations
    ) as data
    GROUP BY created_week, authority_id, group_id
    ORDER BY created_week, authority_id, group_id
) WITH NO DATA;
