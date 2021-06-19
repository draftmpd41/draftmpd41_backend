DROP TABLE IF EXISTS messages;
CREATE TABLE messages (
    mid VARCHAR(50) NOT NULL PRIMARY KEY,
    message VARCHAR(10000) NULL,
    category VARCHAR(100) NULL,
    name VARCHAR(100) NULL,
    mobile VARCHAR(13) NULL,
    email VARCHAR(100) NULL,
    username VARCHAR(100) NULL,
    lat DECIMAL(9,6) NULL,
    lon DECIMAL(9,6) NULL,
    date1 DATE NULL,
    created_on DATETIME NULL,
    modified_on DATETIME NULL,
    modified_by VARCHAR(100) NULL,
    deleted BOOL NULL,
    approved BOOL NULL,
    consent BOOL NULL
);
CREATE INDEX messages_i1 ON messages (date1);
CREATE INDEX messages_i2 ON messages (username);
CREATE INDEX messages_i3 ON messages (approved);
CREATE INDEX messages_i4 ON messages (category);
CREATE INDEX messages_i5 ON messages (consent);
