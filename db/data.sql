REPLACE INTO users VALUES (1, "marketing@samsung.com.au", "Samsung Australia", "https://www.facebook.com/SamsungAustralia", "pw");

REPLACE INTO campaigns VALUES (1, "Galaxy S9", "2018 Flagship Galaxy", "2017-12-01", "2018-13-01", 0, 0.0, 0.0, 0);
REPLACE INTO campaigns VALUES (2, "Post Note 7", "Damage control for Note 7 2016 battery issues", "2016-10-11", "2017-03-03", 0, 0.0, 0.0, 0);


REPLACE INTO user_campaigns VALUES (1,1);
REPLACE INTO user_campaigns VALUES (1,2);
