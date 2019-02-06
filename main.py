try:
    from requests_toolbelt.adapters import appengine
    appengine.monkeypatch()
except ImportError:
    pass

from flask import Flask, render_template, request
#from flask_moment import Moment
from flask_pymongo import PyMongo
import pytz
from pytz import timezone
import datetime
#import json
import requests
from requests_oauthlib import OAuth1
from watson_developer_cloud import NaturalLanguageUnderstandingV1
from watson_developer_cloud.natural_language_understanding_v1 import Features, EmotionOptions


app = Flask(__name__)

app.config['MONGO_DBNAME'] = '<dbname>'
app.config['MONGO_URI'] = 'mongodb://<username>:<password>@ds119503.mlab.com:19503/<dbname>'
mongo = PyMongo(app)


@app.route('/')
def home():
    db_tweets = mongo.db.tweets

    au_tz = pytz.timezone('Australia/Melbourne')
    server_time = datetime.datetime.now(tz=pytz.utc)
    time = server_time.astimezone(au_tz)
    date = time.strftime("%y%m%d")
    display_date = time.strftime("%d %b %Y")
    re_str = '^' + date

    time_labels = []
    sadness = []
    joy = []
    fear = []
    disgust = []
    anger = []

    collection = db_tweets.find({'time': {"$regex": re_str}})
    total = collection.count()

    data = []
    for i in collection:
        data.append(i)

    for item in data:
        # formatting time for webpage display
        unformatted_time = item['time']
        fmt_time_h = unformatted_time[7:9]
        fmt_time_m = unformatted_time[10:12]
        fmt_time = fmt_time_h+":"+fmt_time_m
        time_labels.append(fmt_time)
        sadness.append(item['emotions']['sadness'])
        joy.append(item['emotions']['joy'])
        fear.append(item['emotions']['fear'])
        disgust.append(item['emotions']['disgust'])
        anger.append(item['emotions']['anger'])



    return render_template("home.html",
        display_date=display_date,
                           labels=time_labels, sad_values=sadness, joy_values=joy,
                           fear_values=fear,
                           disgust_values=disgust, anger_values=anger
                           )

@app.route('/radar')
def radar():
    gmap_api_key = "<API_KEY>"
    lat = -37.9712303
    lon = 144.4912816
    result = {}

    return render_template("radar.html", API_KEY=gmap_api_key, lat=lat, lon=lon )


def search_tweet(lat_value, lon_value):
    # Variables that contains the user credentials to access Twitter API
    CONSUMER_KEY = '<key_value>'
    CONSUMER_SECRET = '<key_value>'
    ACCESS_TOKEN = '<key_value>'
    ACCESS_SECRET = '<key_value>'

    auth = OAuth1(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_SECRET)

    url_base = 'https://api.twitter.com/1.1/search/tweets.json?q=&geocode='

    radius = '30km'
    max_count = 30
    url = url_base + lat_value + ',' + lon_value + ',' + radius + '&count=' + str(int(max_count))

    r = requests.get(url, auth=auth)
    response = r.json()

    tweets = ""
    count = 0
    au_tz = timezone('Australia/Melbourne')
    server_time = datetime.datetime.now(tz=pytz.utc)
    time = server_time.astimezone(au_tz)


    # Loop over statuses to store the relevant pieces of information
    if response:
        for status in response['statuses']:
            # Configure the fields you are interested in from the status object
            new_text = status['text']
            tweets = tweets + new_text + " "
            count += 1


    else:
        error = 'Sorry, not results found.'

    return tweets


def analyse_tweet(text):
    natural_language_understanding = NaturalLanguageUnderstandingV1(
        version='2018-11-16',
        iam_apikey='<key_value>',
        url='https://gateway-syd.watsonplatform.net/natural-language-understanding/api'
    )

    response = natural_language_understanding.analyze(
        text=text,
        features=Features(emotion=EmotionOptions(document=["true"])),
        language='en').get_result()

    record = {}
    e = response['emotion']['document']['emotion']
    record['sadness'] = e['sadness']
    record['joy'] = e['joy']
    record['fear'] = e['fear']
    record['disgust'] = e['disgust']
    record['anger'] = e['anger']

    return record





@app.route('/radar_new', methods=["GET", "POST"])
def radar_new():
    gmap_api_key = "<key_value>"



    if request.method == 'POST':
        result = request.form
        lat = result['latitude']
        lon = result['longitude']
        data = search_tweet(lat, lon)
        if(len(data)!=0):
            r = analyse_tweet(data)
            labels = r.keys()
            values = r.values()
            return render_template("radar.html", API_KEY=gmap_api_key, result=result,
                               lat=lat, lon=lon,
                               all=r, labels=labels, values=values)
        else:
            result = {}
            lat = -37.9712303
            lon = 144.4912816
            return render_template("radar.html", API_KEY=gmap_api_key, result=result, lat=lat, lon=lon)

    else:
        result ={}
        lat = -37.9712303
        lon = 144.4912816
        return render_template("radar.html", API_KEY=gmap_api_key, result=result, lat=lat, lon=lon)




if __name__ == '__main__':
    app.run(debug = True)