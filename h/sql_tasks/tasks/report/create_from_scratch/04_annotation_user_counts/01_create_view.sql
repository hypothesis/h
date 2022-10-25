DROP MATERIALIZED VIEW IF EXISTS report.annotation_user_counts CASCADE;

CREATE MATERIALIZED VIEW report.annotation_user_counts AS (
    SELECT
        data.*,
        EXTRACT('year' FROM created_month - INTERVAL '6 month')::smallint AS academic_year,
        CONCAT(
            EXTRACT('year' FROM created_month - INTERVAL '6 month'),
            '-',
            CASE WHEN EXTRACT('quarter' FROM created_month - INTERVAL '6 month') < 3 THEN 1 ELSE 2 END
        ) AS academic_half_year,
        COUNT(1)::integer AS count
    FROM (
        SELECT
            -- Cast to a date as it's 4 bytes instead of 8
            DATE_TRUNC('month', created)::date AS created_month,
            authority_id,
            user_id
        FROM report.annotations
    ) as data
    GROUP BY created_month, authority_id, user_id
    ORDER BY created_month, authority_id, user_id
) WITH NO DATA;
