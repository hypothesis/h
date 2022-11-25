DROP TABLE IF EXISTS report.authorities CASCADE;

CREATE TABLE report.authorities (
    id SMALLINT PRIMARY KEY NOT NULL,
    created DATE NULL,
    authority TEXT NOT NULL
);

CREATE INDEX authorities_authority_idx ON report.authorities (authority);
