DROP INDEX IF EXISTS report.annotation_counts_created_week_authority_id_idx;

REFRESH MATERIALIZED VIEW report.annotation_counts;

ANALYSE report.annotation_counts;

-- A unique index is mandatory for concurrent updates used in the refresh
CREATE UNIQUE INDEX annotation_counts_created_week_authority_id_idx
    ON report.annotation_counts (
        created_week, authority_id, group_id, user_id, sub_type, shared
    );
