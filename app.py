#!flask/bin/python3
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, date
import requests, os
from operator import itemgetter
from itertools import islice
from forms import LoginForm, RegistrationForm, EventForm
from flask_login import LoginManager, current_user, login_user, login_required
from user import User

app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = 'this_is_a_secret'
lm = LoginManager(app)
lm.login_view = '/login'

company = {'name':'COCA-COLA AMATIL LIMITED', 'asx':'CCL', 'fbName':'CocaColaAustralia'}
now = datetime.now()
now_date = now.strftime("%Y-%m-%d")

@lm.user_loader
def load_user(id):
    from db_helpers import query_db
    user = query_db('select * from users where id = %s'%(id), (), True)
    return User(user)

@app.route('/')
def index():
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
        
        user = load_user(user[0])
        login_user(user)
        return redirect('/dashboard')

    return render_template("auth.html", form=login_form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    import db_helpers

    registration_form = RegistrationForm(request.form)
    db = db_helpers.get_db()
    cur = db.cursor()

    if request.method == 'POST' and registration_form.validate():
        result = request.form
        # check that the company doesn't already exist
        
        # make db entry
        #print('insert into users (email, password, companyName, companyUrl) values ("%s", "%s", "%s", "%s")'%(result['email'], result['password'], result['company_name'], result['company_url'])) 

        cur.execute(
                 'insert into users (email, password, companyName, companyUrl) values ("%s", "%s", "%s", "%s")'%(result['email'], result['password'], result['company_name'], result['company_url']) 
                 )
        db.commit()
        return redirect('/login')
    
    return render_template("reg.html", form=registration_form)

@app.route('/dashboard')
@login_required
def dashboard():

    end_date = (subtract_years(now, 1)).strftime("%Y-%m-%d")
    stats = "id,name,website,description,category,fan_count,post_like_count,post_comment_count,post_type,post_message"
    facebook = displayFacebookJSON(company.get('fbName'), end_date+'T00:00:00Z', now_date+'T00:00:00Z', stats)['FacebookStatisticData']

    total_likes = 0
    for post in facebook['posts']:
        total_likes += post['post_like_count']

    facebook_data={}
    facebook_data['num_posts'] = len(facebook['posts'])
    facebook_data['daily_posts'] = round(facebook_data['num_posts']/365, 2)
    facebook_data['avg_react_per_post'] = round(total_likes/facebook_data['num_posts'], 2)

    # should be done by sentiment but whatever
    post_popularity=islice(sort_posts(facebook['posts']), 10)

    return render_template("dashboard.html", company=company, facebook=facebook, facebook_data=facebook_data, post_popularity=post_popularity)

@app.route('/trackCampaigns')
@login_required
def trackCampaigns():
    import db_helpers

    print(current_user.id)
    
    campaigns = db_helpers.query_db('select id, name, start_date, end_date from user_campaigns join campaigns on user_campaigns.campaign_id = campaigns.id where user_id = %s'%(current_user.id))

    print(campaigns)
     

    return render_template("trackCampaigns.html", campaigns = campaigns)

@app.route('/createCampaign', methods=['GET', 'POST'])
@login_required
def createCampaign():
    import db_helpers

    db = db_helpers.get_db()
    create_campaign_form = request.form

    if request.method == 'POST':
        query = db_helpers.query_db('insert into campaigns (name, description, tags, start_date, end_date, comments_target, comments_sentiment_score, likes_target) values ("%s", "%s", "%s", "%s", "%s", %s, %s, %s)'%(
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
def all_campaigns(goals):
    print(goals)
    return render_template("createCampaign.html", goals=goals)

@app.route('/viewCampaign/<campaign_id>', methods=['GET', 'POST'])
def viewCampaign(campaign_id):
    import db_helpers

    print(campaign_id)

    events = db_helpers.query_db('select * from events where campaign = %s'%(campaign_id))

    event_form = EventForm(request.form)

    if request.method == 'POST':
        query = db_helpers.query_db('insert into events (event_name, event_description, event_type, start_date, end_date, campaign) values ("%s", "%s", "%s", "%s", "%s", "%s")'%(
            event_form['event_name'],
            event_form['event_description'],
            event_form['event_type'],
            event_form['start_date'],
            event_form['end_date'],
            campaign_id
            ))    
        return render_template('vewCampaign.html', form = event_form, events = events)
        

    return render_template("viewCampaign.html", form = event_form, events = events)

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

def subtract_years(dt, years):
    try:
        dt = dt.replace(year=dt.year-years)
    except ValueError:
        dt = dt.replace(year=dt.year-years, day=dt.day-1)
    return dt

def sort_posts(posts):
    result = sorted(posts, key=itemgetter('post_like_count'), reverse=True)
    return result

if __name__ == "__main__":
    app.run(debug=True)
