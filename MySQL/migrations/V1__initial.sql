CREATE TABLE IF NOT EXISTS bot_users(
    user_id int not null,
    username varchar(100),
    first_name varchar(100),
    last_name varchar(100),
    PRIMARY KEY (user_id)
);