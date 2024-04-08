CREATE TABLE IF NOT EXISTS api_data(
    query_id BIGINT not null AUTO_INCREMENT,
    title TEXT not null,
    content TEXT,
    uri VARCHAR(1024),
    image VARCHAR(1024),
    PRIMARY KEY (query_id)
);