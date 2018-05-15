drop table if exists users;
create table users(
    id integer primary key autoincrement,
    email string not null,
    companyName string not null,
    companyUrl string not null,
    password string not null
);

drop table if exists campaigns;
create table campaigns(
    id integer primary key autoincrement,
    start_date string not null,
    end_date string not null,
    comments_target integer not null,
    comments_sentiment_score float not null,
    likes_percentage float not null,
    likes_target integer not null
);

drop table is exists user_campaigns;
create table user_campaigns(
    user_id integer references user(id),
    campaign_id integer references campaign(id)
);
