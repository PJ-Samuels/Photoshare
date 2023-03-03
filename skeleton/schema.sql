CREATE DATABASE IF NOT EXISTS photoshare;
USE photoshare;
DROP TABLE IF EXISTS Pictures CASCADE;
DROP TABLE IF EXISTS Albums CASCADE;
DROP TABLE IF EXISTS Users CASCADE;
DROP TABLE IF EXISTS Friends CASCADE;
DROP TABLE IF EXISTS Tags CASCADE;
DROP TABLE IF EXISTS Comments CASCADE;
DROP TABLE IF EXISTS Likes CASCADE;

CREATE TABLE Users (
    user_id int4  AUTO_INCREMENT,
    email varchar(255) UNIQUE,
    password varchar(255),
    fname varchar(255),
    lname varchar(255),
    hometown varchar(255),
    birthday DATE,
    gender varchar(10),
  CONSTRAINT users_pk PRIMARY KEY (user_id)
);

CREATE TABLE Pictures
(
  picture_id int4  AUTO_INCREMENT,
  user_id int4,
  imgdata longblob ,
  caption VARCHAR(255),
  album_id int4,
  INDEX upid_idx (user_id),
  CONSTRAINT pictures_pk PRIMARY KEY (picture_id)
);

CREATE TABLE Albums
(
  album_id int4  AUTO_INCREMENT,
  user_id int4,
  album_name VARCHAR(255),
  INDEX upid_idx (user_id),
  CONSTRAINT album_pk PRIMARY KEY (album_id)
);

CREATE TABLE Friends
(
  user_id int4,
  friend_id int4,
  INDEX upid_idx (user_id),
  CONSTRAINT friends_pk PRIMARY KEY (user_id, friend_id)
);

CREATE TABLE Tags
(
  tag_id int4  AUTO_INCREMENT,
  user_id int4,
  picture_id int4,
  tag_text VARCHAR(255),
  INDEX upid_idx (user_id),
  CONSTRAINT tags_pk PRIMARY KEY (tag_id)
);

CREATE TABLE Comments
(
  comment_id int4  AUTO_INCREMENT,
  user_id int4,
  picture_id int4,
  comment_text VARCHAR(255),
  INDEX upid_idx (user_id),
  CONSTRAINT comments_pk PRIMARY KEY (comment_id)
);

CREATE TABLE Likes
(
  like_id int4  AUTO_INCREMENT,
  user_id int4,
  picture_id int4,
  INDEX upid_idx (user_id),
  CONSTRAINT likes_pk PRIMARY KEY (like_id)
);
INSERT INTO Users (email, password, fname, lname, hometown, birthday,gender) VALUES ('osamuels@bu.edu', '123', 'Oliver', 'Samuels', 'Hyattsville', '2000-10-29','male');
INSERT INTO Users (email, password, fname, lname, hometown, birthday,gender) VALUES ('pjsamuels3@gmail.edu', '123', 'PJ', 'Samuels', 'Hyattsville', '2000-10-29','male');
INSERT INTO Users (email, password, fname, lname, hometown, birthday,gender) VALUES ('test@bu.edu', 'test', 'john', 'doe', 'boston', '2023-02-01','male');
INSERT INTO Users (email, password, fname, lname, hometown, birthday,gender) VALUES ('test1@bu.edu', 'test', 'jane', 'doe', 'boston', '2023-02-01','female');

