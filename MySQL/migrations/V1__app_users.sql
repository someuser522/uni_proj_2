CREATE TABLE IF NOT EXISTS app_users(
    user_id BIGINT NOT NULL AUTO_INCREMENT,
    user_password VARCHAR(100),
    email VARCHAR(100) UNIQUE NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    verification_code TEXT,
    PRIMARY KEY (user_id)
);