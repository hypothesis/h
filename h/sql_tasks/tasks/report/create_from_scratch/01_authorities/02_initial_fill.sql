-- This kind of sucks, but you can't update an enum value in the same
-- transaction you use it. By committing here, we start a new transaction.
-- However we are doing this within listed "destructive" actions, so the impact
-- is less than if we did this on refreshes.
COMMIT;

-- We are adding values to the enum one by one as it allows us to easily
-- maintain this enum by adding more rows if we need to in future

-- Values we care about the most
ALTER TYPE report.authorities ADD VALUE IF NOT EXISTS 'hypothes.is';
ALTER TYPE report.authorities ADD VALUE IF NOT EXISTS 'lms.hypothes.is';
ALTER TYPE report.authorities ADD VALUE IF NOT EXISTS 'lms.ca.hypothes.is';

-- Others
ALTER TYPE report.authorities ADD VALUE IF NOT EXISTS 'test.elifesciences.org';
ALTER TYPE report.authorities ADD VALUE IF NOT EXISTS 'elifesciences.org';
ALTER TYPE report.authorities ADD VALUE IF NOT EXISTS 'hypothesis-publisher-site.herokuapp.com';
ALTER TYPE report.authorities ADD VALUE IF NOT EXISTS 'openlibhums.org';
ALTER TYPE report.authorities ADD VALUE IF NOT EXISTS 'wk.silverchair.com';
ALTER TYPE report.authorities ADD VALUE IF NOT EXISTS 'genesys.com';
ALTER TYPE report.authorities ADD VALUE IF NOT EXISTS 'radicali.io';
ALTER TYPE report.authorities ADD VALUE IF NOT EXISTS 'h.jonudell.info';
ALTER TYPE report.authorities ADD VALUE IF NOT EXISTS 'fuel.press';
ALTER TYPE report.authorities ADD VALUE IF NOT EXISTS 'getqurious.net';
ALTER TYPE report.authorities ADD VALUE IF NOT EXISTS 'mijn.bsl.nl';
ALTER TYPE report.authorities ADD VALUE IF NOT EXISTS 'pathstream.com';
ALTER TYPE report.authorities ADD VALUE IF NOT EXISTS 'temp-h-ca.hypothes.is';
ALTER TYPE report.authorities ADD VALUE IF NOT EXISTS 'app.noodlecase.com';
ALTER TYPE report.authorities ADD VALUE IF NOT EXISTS 'allenai.org';
ALTER TYPE report.authorities ADD VALUE IF NOT EXISTS 'csepub.com';
