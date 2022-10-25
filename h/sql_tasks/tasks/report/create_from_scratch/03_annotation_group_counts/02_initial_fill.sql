DROP INDEX IF EXISTS report.annotation_group_counts_created_week_authority_id_group_id_idx;
DROP INDEX IF EXISTS report.annotation_group_counts_created_week_idx;

REFRESH MATERIALIZED VIEW report.annotation_group_counts;

ANALYSE report.annotation_group_counts;

-- A unique index is mandatory for concurrent updates used in the refresh
CREATE UNIQUE INDEX annotation_group_counts_created_week_authority_id_group_id_idx ON report.annotation_group_counts (authority_id, created_week, group_id);
CREATE INDEX annotation_group_counts_created_week_idx ON report.annotation_group_counts USING BRIN (created_week);
