-- You can get values to maintain this table with the following query:

-- SELECT
--     -- Create a fake "primary" key
--     created::date,
--     authority
-- FROM (
--     SELECT
--         authority,
--         MIN(created) as created
--     FROM "group"
--     GROUP BY authority
--     ORDER BY created
-- ) as data

-- These values are required to be globally unique

TRUNCATE report.authorities;

INSERT INTO report.authorities (id, created, authority)
VALUES
    -- Values we care about the most
    (1, '2015-09-22', 'hypothes.is'),
    (2, '2018-10-12', 'lms.hypothes.is'),
    (3, '2022-01-21', 'lms.ca.hypothes.is'),

    -- Others
    (1001, '2017-04-28', 'test.elifesciences.org'),
    (1002, '2017-11-28', 'elifesciences.org'),
    (1003, '2018-02-01', 'hypothesis-publisher-site.herokuapp.com'),
    (1004, '2018-05-01', 'openlibhums.org'),
    (1005, '2018-11-26', 'wk.silverchair.com'),
    (1006, '2018-12-13', 'genesys.com'),
    (1007, '2019-03-29', 'radicali.io'),
    (1008, '2019-07-08', 'h.jonudell.info'),
    (1009, '2019-11-15', 'fuel.press'),
    (1010, '2020-02-24', 'getqurious.net'),
    (1011, '2020-07-08', 'mijn.bsl.nl'),
    (1012, '2021-04-21', 'pathstream.com'),
    (1013, '2021-06-15', 'temp-h-ca.hypothes.is'),
    (1014, '2021-08-10', 'app.noodlecase.com'),
    (1015, '2021-12-15', 'allenai.org'),
    (1016, '2022-04-08', 'csepub.com');

ANALYSE report.authorities;
