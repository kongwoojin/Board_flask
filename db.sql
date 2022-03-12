-- auto-generated definition
create table article
(
    id       int auto_increment
        primary key,
    title    varchar(30) null,
    text     text        null,
    writerId varchar(20) null,
    date     datetime    null
);