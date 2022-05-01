create table article
(
    id         int auto_increment
        primary key,
    title      varchar(30)   null,
    text       text          null,
    username   varchar(20)   null,
    date       datetime      null,
    view_count int default 0 not null,
    writer_id  int           not null
);

create table comments
(
    id         int auto_increment
        primary key,
    comment    text null,
    article_id int  not null,
    reply_to   int  null,
    writer_id  int  not null
);

create table users
(
    id       int auto_increment
        primary key,
    userid   varchar(30) null,
    password char(128)   null,
    username varchar(20) null,
    email    varchar(50) null
);