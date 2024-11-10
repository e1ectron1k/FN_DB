CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE words (
    word_id SERIAL PRIMARY KEY,
    word VARCHAR(50),
    translation VARCHAR(50)
);

CREATE TABLE user_words (
    user_word_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    word_id INTEGER REFERENCES words(word_id)
);

INSERT INTO words (word, translation) VALUES
('red', 'красный'),
('blue', 'синий'),
('green', 'зелёный'),
('he', 'он'),
('she', 'она'),
('it', 'это'),
('I', 'я'),
('you', 'ты'),
('we', 'мы'),
('they', 'они');
