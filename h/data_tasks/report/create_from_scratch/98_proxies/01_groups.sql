DROP VIEW IF EXISTS report.groups CASCADE;

-- Create a proxy view to isolate LMS from reading our data directly
CREATE VIEW report.groups AS (
    SELECT
        id,
        authority,
        authority_provided_id,
        name,
        created
    FROM "group"
);
