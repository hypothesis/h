DROP INDEX IF EXISTS report.annotation_user_counts_created_week_authority_id_user_id_idx;
DROP INDEX IF EXISTS report.annotation_user_counts_created_week_idx;

REFRESH MATERIALIZED VIEW report.annotation_user_counts;

ANALYSE report.annotation_user_counts;

-- A unique index is mandatory for concurrent updates used in the refresh
CREATE UNIQUE INDEX annotation_user_counts_created_week_authority_id_user_id_idx ON report.annotation_user_counts (authority_id, created_week, user_id);
CREATE INDEX annotation_user_counts_created_week_idx ON report.annotation_user_counts USING BRIN (created_week);
