CREATE TABLE IF NOT EXISTS user_query_stats(
    id BIGINT NOT NULL AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    query_id BIGINT NOT NULL,
    query_count INT NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES bot_users(user_id),
    FOREIGN KEY (query_id) REFERENCES query_stats(query_id)
);
