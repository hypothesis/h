DROP TYPE IF EXISTS report.timescale CASCADE;

CREATE TYPE report.timescale AS ENUM (
    'week', 'month', 'semester', 'academic_year', 'year', 'all_time'
);

DROP MATERIALIZED VIEW IF EXISTS report.authority_activity CASCADE;

CREATE MATERIALIZED VIEW report.authority_activity AS (
    WITH
        -- Build up the facets to divide the queries up by

        weeks AS (
            SELECT DISTINCT(created_week) AS timestamp_week
            FROM report.annotation_user_counts
        ),

        timescales AS (
            SELECT column1 AS timescale FROM (
                VALUES ('week'), ('month'), ('semester'), ('academic_year'), ('year'), ('all_time')
            ) AS data
        ),

        periods AS (
            SELECT
                timestamp_week,
                timescale::report.timescale,
                report.multi_truncate(timescale, timestamp_week) AS period
            FROM weeks
            CROSS JOIN timescales
        ),

        -- Start calculating individual metrics

        annotating_users AS (
            SELECT
                period,
                timescale,
                authority_id,
                COUNT(DISTINCT(user_id)) AS annotating_users
            FROM periods
            JOIN report.annotation_user_counts ON
                annotation_user_counts.created_week = periods.timestamp_week
            GROUP BY
                period, timescale, authority_id
        ),

        users AS (
            SELECT
                users.id AS user_id,
                authorities.id AS authority_id,
                DATE_TRUNC('week', users.registered_date)::DATE AS registered_week
            FROM "user" AS users
            JOIN report.authorities ON
                authorities.authority = users.authority
        ),

        registering_users AS (
            SELECT
                period,
                timescale,
                authority_id,
                COUNT(DISTINCT(user_id)) AS registering_users
            FROM periods
            JOIN users ON
                users.registered_week = periods.timestamp_week
            GROUP BY period, timescale, authority_id
        ),

        annotations AS (
            SELECT
                period,
                timescale,
                authority_id,
                SUM(shared) AS shared_annotations,
                SUM(replies) AS reply_annotations,
                SUM(count) AS annotations
            FROM periods
            JOIN report.annotation_group_counts ON
                annotation_group_counts.created_week = periods.timestamp_week
            GROUP BY period, timescale, authority_id
        )

    -- Fuse all the metrics together as separate columns

    SELECT
        -- Date related
        timescale,
        period::DATE AS start_date,
        (period + report.single_interval(timescale::text))::DATE AS end_date,
        report.present_date(timescale::text, period) AS period,
        -- The major entity identifier
        authority_id,
        -- Metrics
        COALESCE(MAX(annotating_users), 0) as annotating_users,
        COALESCE(MAX(registering_users), 0) as registering_users,
        COALESCE(MAX(total_users), 0) as total_users,
        COALESCE(MAX(shared_annotations), 0) as shared_annotations,
        COALESCE(MAX(reply_annotations), 0) as reply_annotations,
        COALESCE(MAX(annotations), 0) as annotations
    FROM (
        SELECT
            period, timescale, authority_id,
            0 AS annotating_users,
            registering_users.registering_users,
            -- Total users are just the sum of registering users over time, we
            -- could try and do this in Metabase, but it's easier for all if
            -- it's available as primary data
            SUM(registering_users) OVER (
                PARTITION BY timescale, authority_id ORDER BY period
            ) AS total_users,
            0 AS shared_annotations, 0 AS reply_annotations, 0 AS annotations
        FROM registering_users

        UNION ALL

        SELECT
            period, timescale, authority_id,
            annotating_users, 0, 0,
            0, 0, 0
        FROM annotating_users

        UNION ALL

        SELECT
            period, timescale, authority_id,
            0, 0, 0,
            shared_annotations, reply_annotations, annotations
        FROM annotations
    ) AS data
    GROUP BY timescale, period, authority_id
    ORDER BY timescale, period, authority_id
) WITH NO DATA;
