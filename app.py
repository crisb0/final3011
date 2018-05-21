#!flask/bin/python3
from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
from datetime import datetime, date, timedelta
import requests, os
from operator import itemgetter
from itertools import islice
from forms import LoginForm, RegistrationForm, EventForm 
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from user import User
#import sentiment
import re

app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = 'this_is_a_secret'
lm = LoginManager(app)

company = {'name':'COCA-COLA AMATIL LIMITED', 'asx':'CCL', 'fbName':'CocaColaAustralia'}
now = datetime.now()
now_date = now.strftime("%Y-%m-%d")

@lm.user_loader
def load_user(id):
    from db_helpers import query_db
    user = query_db('select * from users where id = %s'%(id), (), True)
    return User(user) if user else None

@app.route('/')
def index():
    #print(current_user)
    return render_template("index.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    from db_helpers import query_db

    login_form = LoginForm(request.form)

    if request.method == 'POST' and login_form.validate():
        result = request.form
        #print('select * from users where email = %s and password = %s' % (result['email'], result['password']))
        user = query_db('select * from users where email = "%s" and password = "%s"' % (result['email'], result['password']), (), True)
        
        if user is None:
            print('Invalid credentials')
            return redirect('/login')

        userid = user[0] 
        user = load_user(user[0])


        login_user(user)
        return redirect('/trackCampaigns')

    return render_template("auth.html", form=login_form)

@app.route('/logout')  
def logout():  
    logout_user()  
    return redirect(url_for('index'))  

@app.route('/register', methods=['GET', 'POST'])
def register():
    import db_helpers
    from db_helpers import query_db

    registration_form = RegistrationForm(request.form)
    db = db_helpers.get_db()
    cur = db.cursor()

    if request.method == 'POST' and registration_form.validate():
        result = request.form
        # check that the company doesn't already exist
        
        # make db entry
        #print('insert into users (email, password, companyName, companyUrl) values ("%s", "%s", "%s", "%s")'%(result['email'], result['password'], result['company_name'], result['company_url'])) 

        cur.execute(
                 'insert into users (email, password, companyName, companyWebsite, companyFacebook) values ("%s", "%s", "%s", "%s", "%s")'%(result['email'], result['password'], result['company_name'], result['company_website'], result['company_facebook'])
                 )
        db.commit()
        #log in user straight away
        user = query_db('select * from users where email = "%s" and password = "%s"' % (result['email'], result['password']), (), True)
        user = load_user(user[0])
        login_user(user)
        return redirect('/trackCampaigns')

    return render_template("reg.html", form=registration_form)

@app.route('/dashboard')
@login_required
def dashboard():
    import db_helpers
    from db_helpers import query_db
    
    user = load_user(current_user.id)
    match = re.search(r"facebook\.com/(\w+).*", user.companyFacebook)
    print(user.companyFacebook)
    print(match)
    facebookName = match.group(1)
    campaigns = db_helpers.query_db('select distinct id, name, start_date, end_date, tags from user_campaigns join campaigns on user_campaigns.campaign_id = campaigns.id where user_id = %s'%(user.id))

    
    end_date = (subtract_years(now, 1)).strftime("%Y-%m-%d")
    stats = "id,name,website,description,category,fan_count,post_like_count,post_comment_count,post_type,post_message"
    facebook = displayFacebookJSON(facebookName, end_date+'T00:00:00Z', now_date+'T00:00:00Z', stats)['FacebookStatisticData']
    #how you would use filterPosts
    fb = filterPosts(campaigns[0][4], facebook)

    total_likes = 0
    for post in fb['posts']:
        total_likes += post['post_like_count']

    facebook_data={}
    facebook_data['num_posts'] = len(fb['posts'])
    facebook_data['daily_posts'] = round(facebook_data['num_posts']/365, 2)
    facebook_data['avg_react_per_post'] = round(total_likes/facebook_data['num_posts'], 2)

    # should be done by sentiment but whatever
    post_popularity=islice(sort_posts(fb['posts']), 10)

    return render_template("dashboard.html", company=company, facebook=fb, facebook_data=facebook_data, post_popularity=post_popularity)

@app.route('/trackCampaigns')
@login_required
def trackCampaigns():
    import db_helpers
    from db_helpers import query_db

    print(current_user.id)
    campaigns = db_helpers.query_db('select distinct id, name, start_date, end_date, tags from user_campaigns join campaigns on user_campaigns.campaign_id = campaigns.id where user_id = %s'%(current_user.id))
    campaigns_list = list()
    print(campaigns)
    for campaign in campaigns:
        t = list(campaign)
        #print(t)
        campaigns_list.append(t)
   # print(now)

    for campaign in campaigns_list:
        if(datetime.strptime(str(campaign[3]), "%Y-%m-%d") > now):
            campaign.append("in_progress")
        else:
            campaign.append("ended")
    #print(campaigns_list)
    user = query_db('select * from users where id = %d' % (current_user.id), (), True)
    return render_template("trackCampaigns.html", campaigns = campaigns_list, user = user)

@app.route('/createCampaign', methods=['GET', 'POST'])
@login_required
def createCampaign():
    import db_helpers

    db = db_helpers.get_db()
    create_campaign_form = request.form

    if request.method == 'POST':
        query = db_helpers.query_db('insert into campaigns (name, description, tags, start_date, end_date, comments_target, sentiment_score, likes_target) values ("%s", "%s", "%s", "%s", "%s", %s, %s, %s)'%(
            create_campaign_form['campaign_name'],
            create_campaign_form['campaign_description'],
            create_campaign_form['tags'],
            create_campaign_form['start_date'],
            create_campaign_form['end_date'],
            create_campaign_form['comment_count'],
            create_campaign_form['sentiment_score'],
            create_campaign_form['like_count']
            ))
        db.commit()

        campaign_id = db_helpers.query_db('select id from campaigns where name = "%s"'%(create_campaign_form['campaign_name']), (), True)

        query = db_helpers.query_db('insert into user_campaigns (user_id, campaign_id) values (%s, %s)'%(current_user.id, campaign_id[0]))
        db.commit()

        return render_template("createCampaign.html")

    return render_template("createCampaign.html")

@app.route('/campaigns', methods=['GET', 'POST'])
@login_required
def all_campaigns(goals):
    print(goals)
    return render_template("createCampaign.html", goals=goals)

@app.route('/viewCampaign', methods=['GET', 'POST'])
@login_required
def viewCampaign():
    import db_helpers
    db = db_helpers.get_db()
    campaign_id = request.args.get('campaign_id')

    # get events
    events = return_events(int(campaign_id))
    #overwrite events.json
    with open("events.json", "w") as jsonFile:
        json.dump(events, jsonFile)

    user = load_user(current_user.id)
    match = re.search(r"facebook\.com/(\w+).*", user.companyFacebook)
    facebookName = match.group(1)
    campaign = db_helpers.query_db('select * from campaigns where id = %s'%(campaign_id))
    #print(campaign)
    if(datetime.strptime(campaign[0][4], "%Y-%m-%d") > now):
        campaign.append("in_progress")
    else:
        campaign.append("ended")
    sentiments = get_all_weeks(facebookName,campaign[0][3],campaign[0][4])
	
    ###

    end_date = campaign[0][4]
    start_date = campaign[0][3]
    stats = "id,name,website,description,category,fan_count,post_like_count,post_comment_count,post_type,post_message"

    facebook = displayFacebookJSON(facebookName, start_date+'T00:00:00Z', end_date+'T00:00:00Z', stats)['FacebookStatisticData']

    fb = filterPosts(campaign[0][5], facebook)

    total_likes = 0
    for post in fb['posts']:
        total_likes += post['post_like_count']
    
    campaign_length = datetime.strptime(campaign[0][3], "%Y-%m-%d") - datetime.strptime(campaign[0][4], "%Y-%m-%d")
    c_len = campaign_length.days
    facebook_data={}
    facebook_data['num_posts'] = len(fb['posts'])
    facebook_data['daily_posts'] = round(facebook_data['num_posts']/c_len, 2)
    facebook_data['avg_react_per_post'] = round(total_likes/facebook_data['num_posts'], 2)

    # should be done by sentiment but whatever
    post_popularity=islice(sort_posts(fb['posts']), 5)
    content = sort_posts(fb['posts'])[0]['post_type']
    ###

    event_form = EventForm(request.form)

    if request.method == 'POST':
        q = 'insert into events values (null, "%s", "%s", "%s", "%s", "%s", "    %s")' % (
             getval(event_form['event_name']),
             getval(event_form['event_description']),
             getval(event_form['event_type']),
             getval(event_form['start_date']),
             getval(event_form['end_date']),
             campaign_id
             )
        query = db_helpers.query_db(q)
        db.commit()

        return render_template('viewCampaign.html', form = event_form, events = events, campaign = campaign, sentiments=sentiments, facebook=facebook, facebook_data=facebook_data, post_popularity=post_popularity, content=content)

        #return render_template("viewCampaign.html", form = event_form, events = events, campaign = campaigns)

def getval(string):
    print(string)
    match = re.search( r'value="(.+)"', str(string))
    return match.group(1)

def return_events(campaign_id):
    import db_helpers
    events = db_helpers.query_db('select * from events where campaign = %s' % (campaign_id))
    events_list = []
    for event in events:
        event_dict = {"title": event[1], "start": event[4], "end": event[5]}
        events_list.append(event_dict)
    return events_list 


@app.route('/data')
def return_data():
    start_date = request.args.get('start', '')
    end_date = request.args.get('end', '')
    campaign_id = request.args.get('campaign_id')
    print(campaign_id)
    with open("events.json", "r") as input_data:
        return input_data.read()

@app.route('/compareCampaigns', methods=['GET', 'POST'])
@login_required
def compareCampaigns():
    import db_helpers

    if request.method == 'POST':
        to_compare = request.form
        campaign1 = to_compare['campaign1']
        campaign2 = to_compare['campaign2']
        print("campaign 1 is ", campaign1)
        print("campaign 2 is ", campaign2)
        query1 = db_helpers.query_db('select * from campaigns where name = "%s"'%(campaign1))
        query2 = db_helpers.query_db('select * from campaigns where name = "%s"'%(campaign2))
        print("campaign: ", query1)
        if(datetime.strptime(query1[0][4], "%Y-%m-%d") > now):
            query1.append("in_progress")
        else:
            query1.append("ended")
        if(datetime.strptime(query2[0][4], "%Y-%m-%d") > now):
            query2.append("in_progress")
        else:
            query2.append("ended")
        return render_template("compareCampaigns.html", c1 = query1, c2 = query2)
    return render_template("compareCampaigns.html", c1 = [], c2 = [])

@app.route('/editCampaign/<campaign_id>', methods=['GET', 'POST'])
def editCampaign(campaign_id):
    import db_helpers

    db = db_helpers.get_db()
    print(campaign_id)
    campaign = db_helpers.query_db('select * from campaigns where id = %s'%(campaign_id))
    print("campaign is", campaign)

    events = db_helpers.query_db('select * from events where campaign = %s'%(campaign_id))
    edit_campaign_form = request.form

    if request.method == 'POST':
        query = db_helpers.query_db('update campaigns set name = "%s", description = "%s", tags = "%s", start_date = "%s", end_date = "%s", comments_target = "%s", sentiment_score = "%s", likes_target = "%s" where id=%s'%(
            edit_campaign_form['campaign_name'],
            edit_campaign_form['campaign_description'],
            edit_campaign_form['tags'],
            edit_campaign_form['start_date'],
            edit_campaign_form['end_date'],
            edit_campaign_form['comment_count'],
            edit_campaign_form['sentiment_score'],
            edit_campaign_form['like_count'],
            campaign_id
            ))
        db.commit()
        q1 = db_helpers.query_db('select * from campaigns where id = %s'%(campaign_id))

    return render_template("editCampaign.html", campaign=campaign)
# add any other routes above

#helper methods
def displayStocksJSON(id, date, lower, upper):
    result = requests.get("http://team-distribution.info/api/v3/returns?id=%s&date=%s&varlist=CM_Return&lower=%s&upper=%s" % (id, date, lower, upper)).json()
    return result

def displayFacebookJSON(page, start, end, stats):
    print("Displaying JSON...")
    print("query: " + "http://qt314.herokuapp.com/v2/company/%s?start_date=%s&end_date=%s&stats=%s" % (page, start, end, stats))
    result =  requests.get("http://qt314.herokuapp.com/v2/company/%s?start_date=%s&end_date=%s&stats=%s" % (page, start, end, stats)).json()
    print("Query successful")
    print(result)
    # making the time look nice
    if 'posts' in result:
        print("POSTS HERE")
        for i in result['posts']:
            if 'post_created_time' in i:
                temp = re.sub('[a-zA-Z]', ' ', i['post_created_time'])
                temp = re.sub('\+.*$', '', temp)
                i['post_created_time'] = temp

    if 'Website' in result:
        result['Website'] = re.sub('.*//', '', result['Website'])
    
    return result

# input: string in the form of "x,y,a" and facebook data as a tuple
# output: dict of facebook data 
def filterPosts(searchQuery, facebookData):
    #make sure query is regex friendly
    q = re.sub(r'\s*,\s*', '|', searchQuery, flags=re.IGNORECASE)

    #convert the tuple to a dict
    result = dict(facebookData)
    relevantPosts = list()
    print(result)
    #filter posts to see which are relevant
    for post in result['posts']:
        print("\n\n\n")
        if('post_message') in post:
            if(re.search(q, post['post_message'], flags=re.IGNORECASE)):
                p = dict(post)
                relevantPosts.append(p)
    #add our relevant posts
    result['posts'] = relevantPosts
    #return dict with information
    return result

def subtract_years(dt, years):
    try:
        dt = dt.replace(year=dt.year-years)
    except ValueError:
        dt = dt.replace(year=dt.year-years, day=dt.day-1)
    return dt

def sort_posts(posts):
    result = sorted(posts, key=itemgetter('post_like_count'), reverse=True)
    return result

def get_week_comment(page, end , week):
    enddate = datetime.strptime(end , "%Y-%m-%dT%H:%M:%SZ")
    d = timedelta(weeks=week)
    startdate = enddate - d
    rq_string = create_fb_request(page,startdate, enddate)
    page_stats = requests.get(rq_string).json() 
    text = "neutral" 
    if "data" in page_stats:
        for x in page_stats["data"]:
            if "comments" in x:
                if "data" in x["comments"]:
                    for y in x["comments"]["data"]:
                        text += y["message"] + "\n" if "message" in y else ""

    # sentiment analysis can only process up to 100k character 
    return text[:100000]
def create_fb_request(page_name, start_time, end_time):
    access_token = os.environ.get('FB_API_KEY')
    request_string = "https://graph.facebook.com/v2.12/%s/posts?fields=comments.since(%s).until(%s)&access_token=%s" % (page_name,start_time.timestamp(),end_time.timestamp(),access_token)
    return request_string
def get_all_weeks(page_name,frm,to):
    fromTime = datetime.strptime(frm , "%Y-%m-%d")
    toTime = min(datetime.strptime(to , "%Y-%m-%d"),now)
    d = timedelta(weeks=1)
    scores = []
    while fromTime <= toTime:
        scores.append(get_score_for_week(page_name,datetime.strftime(fromTime, "%Y-%m-%dT%H:%M:%SZ")))
        fromTime += d
    return scores

    
def get_score_for_week(page_name,time):
    from db_helpers import query_db, get_db
    query1 = query_db('select score from sentiments where company_name = "%s" and start_date="%s"'%(page_name,time), one=True)
    if query1 is None: 
      comments = get_week_comment(page_name,time, 5)
      score = sentiment.get_sentiment(comments)
      db = get_db()
      cur = db.cursor()
      cur.execute('insert into sentiments (company_name, start_date, score) values ("%s", "%s", %f)' % (page_name,time,score))
      db.commit()
      return score
    else:
      return query1[0]
#print(test)


if __name__ == "__main__":
    app.run(debug=True)

#test = get_score_for_week("Telstra", "2018-01-01T00:00:00Z")
#print(test)
#print(sentiment.get_sentiment(test))
