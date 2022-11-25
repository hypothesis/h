-- A function for truncating dates that accepts the same resolutions as
-- DATE_TRUNC(), but also accepts:
--
-- * all_time - Returning an arbitrary date in the past
-- * academic_year - Truncating to the start of the academic year
-- * semester - Truncating to the nearest 6 months

CREATE OR REPLACE FUNCTION report.multi_truncate(resolution TEXT, date DATE)
RETURNS DATE
IMMUTABLE
AS $$
    SELECT CASE
        WHEN resolution = 'all_time' THEN '1901-01-01'::DATE
        WHEN resolution = 'academic_year' THEN (DATE_TRUNC('year', date - INTERVAL '6 month') + INTERVAL '6 month')::DATE
        WHEN resolution = 'semester' THEN (DATE_TRUNC('year', date) + (
            CASE
                WHEN EXTRACT('quarter' FROM date) < 3 THEN INTERVAL '0 months'
                ELSE INTERVAL '6 months'
            END
        ))::DATE
        ELSE DATE_TRUNC(resolution, date)::date
    END
$$
LANGUAGE SQL;

-- A function for getting intervals. This accepts the same resolutions as
-- `report.multi_truncate` above.

CREATE OR REPLACE FUNCTION report.single_interval(resolution TEXT)
RETURNS INTERVAL
IMMUTABLE
AS $$
    SELECT CASE
        -- Our start date for "all time" is '1901' so add 200 years to ensure
        -- the other end is far in the future
        WHEN resolution = 'all_time' THEN INTERVAL '200 years'
        WHEN resolution = 'year' THEN INTERVAL '1 year'
        WHEN resolution = 'academic_year' THEN INTERVAL '1 year'
        WHEN resolution = 'semester' THEN INTERVAL '6 months'
        WHEN resolution = 'quarter' THEN INTERVAL '3 months'
        WHEN resolution = 'month' THEN INTERVAL '1 month'
        WHEN resolution = 'week' THEN INTERVAL '7 days'
        WHEN resolution = 'day' THEN INTERVAL '1 day'
    END
$$
LANGUAGE SQL;

-- A function for representing dates at various resolutions. This will create
-- a human readable version of a date as follows:
--
-- * all_time - The string "All time"
-- * academic_year - YYYY
-- * year - YYYY
-- * semester - YYYY-S
-- * month - YYYY-MM-DD
-- * week - YYYY-MM-DD

CREATE OR REPLACE FUNCTION report.present_date(resolution TEXT, date DATE)
RETURNS TEXT
IMMUTABLE
AS $$ SELECT
    CASE
        WHEN resolution = 'all_time' THEN 'All time'
        WHEN resolution = 'academic_year' THEN TO_CHAR(date - INTERVAL '6 month', 'YYYY')
        WHEN resolution = 'semester' THEN CONCAT(
            EXTRACT('year' FROM date - INTERVAL '6 month'),
            '-',
            CASE
            WHEN EXTRACT('quarter' FROM date - INTERVAL '6 month') < 3
                THEN 1
            ELSE 2 END
        )
        WHEN resolution = 'year' THEN TO_CHAR(date, 'YYYY')
        WHEN resolution = 'month' THEN TO_CHAR(date, 'YYYY-MM')
        ELSE date::TEXT
    END
$$
LANGUAGE SQL;
