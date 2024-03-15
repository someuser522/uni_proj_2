CREATE TABLE IF NOT EXISTS query_stats(
    query_id BIGINT not null AUTO_INCREMENT,
    query_txt varchar(500) not null,
    times_used int not null DEFAULT 1,
    PRIMARY KEY (query_id)
);