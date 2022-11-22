DROP INDEX IF EXISTS report.authority_activity_timescale_period_authority_id_idx;

REFRESH MATERIALIZED VIEW report.authority_activity;

ANALYSE report.authority_activity;

-- A unique index is mandatory for concurrent updates used in the refresh
CREATE UNIQUE INDEX authority_activity_timescale_period_authority_id_idx ON report.authority_activity (timescale, period, authority_id);
