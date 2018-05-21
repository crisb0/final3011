REPLACE INTO users VALUES (1, "marketing@samsung.com.au", "Samsung Australia","http://www.samsung.com/au/", "https://www.facebook.com/SamsungAustralia", "pw");

REPLACE INTO campaigns VALUES (1, "Galaxy S9", "2018 Flagship Galaxy", "2017-01-12", "2018-03-12","GalaxyS9", 200, 1.0, 205);
REPLACE INTO campaigns VALUES (2, "Post Note 7", "Damage control for Note 7 2016 battery issues", "2016-10-11", "2017-03-03","", 0, 0.0, 0);

REPLACE INTO user_campaigns VALUES (1,1);
REPLACE INTO user_campaigns VALUES (1,2);

REPLACE INTO events values(1, 'S9 Launch', '2017 Launch Conference for Samsung Galaxy S9', 'conference', '2018-03-11', '2018-03-11', 1);
REPLACE INTO events values(2, 'TEST', 'TEST', 'TEST', '2018-05-22', '2018-05-22', 1);
