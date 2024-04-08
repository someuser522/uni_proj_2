CREATE TABLE IF NOT EXISTS V1__users(
    user_id BIGINT NOT NULL,
    pass varchar(100),
    email varchar(100),
    email_verified varchar(100),
    PRIMARY KEY (user_id)
);