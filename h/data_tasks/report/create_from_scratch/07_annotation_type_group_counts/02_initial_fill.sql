DROP INDEX IF EXISTS report.annotation_type_group_counts_created_week_authority_id_idx;

REFRESH MATERIALIZED VIEW report.annotation_type_group_counts;

ANALYSE report.annotation_type_group_counts;

-- A unique index is mandatory for concurrent updates used in the refresh
CREATE UNIQUE INDEX annotation_type_group_counts_created_week_authority_id_idx
    ON report.annotation_type_group_counts (created_week, authority_id, group_id, sub_type, shared);
