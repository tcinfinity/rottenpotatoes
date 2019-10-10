SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS movies;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS confirmationEmail;
DROP TABLE IF EXISTS descriptions;

CREATE TABLE movies (
  id varchar(9) NOT NULL UNIQUE PRIMARY KEY,
  title varchar NOT NULL,
  year int NOT NULL,
  runtime int NOT NULL,
  imdbRating float NOT NULL,
  rpRating float
);

CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  username varchar(20) NOT NULL UNIQUE,
  email varchar NOT NULL UNIQUE,
  password varchar(255) NOT NULL,
  uuid varchar(128) NOT NULL UNIQUE,
  ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE confirmationEmail (
  id int NOT NULL UNIQUE,
  key varchar(128) NOT NULL UNIQUE,
  CONSTRAINT fk_category
  FOREIGN KEY (id)
    REFERENCES users(id)
);

CREATE TABLE reviews (
  movieID varchar(9) NOT NULL,
  username varchar(20) NOT NULL,
  rating float NOT NULL CHECK(rating >= 1 and rating <= 10),
  mdata TEXT NOT NULL,
  ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (movieID) REFERENCES movies(id),
  FOREIGN KEY (username) REFERENCES users(username)
);