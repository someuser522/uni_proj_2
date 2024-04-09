CREATE TABLE IF NOT EXISTS app_users(
    user_id BIGINT NOT NULL,
    user_password VARCHAR(100),
    email VARCHAR(100) UNIQUE NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (user_id)
);