CREATE TABLE IF NOT EXISTS query_stats(
    query_id BIGINT NOT NULL AUTO_INCREMENT,
    query_txt varchar(500) NOT NULL,
    times_used INT NOT NULL DEFAULT 1,
    PRIMARY KEY (query_id)
);