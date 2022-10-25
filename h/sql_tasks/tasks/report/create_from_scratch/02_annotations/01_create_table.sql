DROP TABLE IF EXISTS report.annotations CASCADE;

CREATE TABLE report.annotations (
    id SERIAL PRIMARY KEY,
    uuid UUID NOT NULL,
    user_id INT NOT NULL,
    group_id INT NOT NULL,
    document_id INT NOT NULL,
    authority_id SMALLINT NOT NULL,
    created DATE NOT NULL,
    updated TIMESTAMP NOT NULL,
    deleted BOOLEAN NOT NULL,
    shared BOOLEAN NOT NULL,
    size INT,
    parent_uuids UUID[],
    tags TEXT[]
);
