from yoyo import step

steps = [
    step(
        'CREATE TABLE users ('
        '   id SERIAL PRIMARY KEY,'
        '   telegram_id INTEGER NOT NULL UNIQUE'
        ')'
    ),
    step(
        'CREATE TABLE feeds ('
        '   id SERIAL PRIMARY KEY,'
        '   url TEXT NOT NULL UNIQUE'
        ')'
    ),
    step(
        'CREATE TABLE subscriptions ('
        '   user_id INTEGER REFERENCES users,'
        '   feed_id INTEGER REFERENCES feeds,'
        '   UNIQUE (user_id, feed_id)'
        ')'
    ),
    step(
        'CREATE TABLE feeds_last_items ('
        '   feed_id INTEGER REFERENCES feeds ON DELETE CASCADE,'
        '   url TEXT NOT NULL,'
        '   guid TEXT'
        ')'
    )
]
