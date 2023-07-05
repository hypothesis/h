DROP VIEW IF EXISTS report.users CASCADE;

-- Create a proxy view to isolate LMS from reading our data directly
CREATE VIEW report.users AS (
    SELECT
        id,
        username,
        authority,
        registered_date
    FROM "user"
);
