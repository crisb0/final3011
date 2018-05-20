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
    name string not null,
    description string not null,
    tags string not null,
    start_date string not null,
    end_date string not null,
    comments_target integer not null,
    comments_sentiment_score float not null,
    likes_target integer not null
);

drop table if exists user_campaigns;
create table user_campaigns(
    user_id integer references user(id),
    campaign_id integer references campaign(id)
);

drop table if exists events;
create table events(
    id integer primary key autoincrement,
    event_name string not null,
    event_description string not null,
    event_type string not null,
    start_date string not null,
    end_date sting not null,
    campaign integer references campaign(id)
);
