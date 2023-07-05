DROP VIEW IF EXISTS report.user_group CASCADE;

-- Create a proxy view to isolate LMS from reading our data directly
CREATE VIEW report.user_group AS (
    SELECT
        user_id,
        group_id
    FROM user_group
);
