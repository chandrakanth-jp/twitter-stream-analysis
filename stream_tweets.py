"""
enables access to real-time tweets using Twitter API
"""
import json
import time
import tweepy
from decouple import config 
from transformers import pipeline
import pymongo


def auth():
    """Autheticate user's Twitter API keys"""
    try:
        oauth = tweepy.OAuthHandler(config("API_KEY"), config("API_SEC"))
        oauth.set_access_token(config("ACS_TOK"), config("ACS_TOK_SEC"))
        api = tweepy.API(oauth, wait_on_rate_limit=True)
    except tweepy.TweepError:
        print("API authentication error!")
    
    return api


class MyStreamListener(tweepy.StreamListener):
    """
    Class for streaming tweets and storing to MongoDB.

    Attributes
    ----------
    keywords: str
            list of keywords to search
    database: MongoClient instance

    collection: str
            name of collection
    """

    def __init__(self, keywords, database, collection):
        self.tweet_analyser = pipeline("sentiment-analysis",model="cardiffnlp/twitter-roberta-base-sentiment")
        self.keywords = keywords
        self.database = database
        self.collection = collection
        super().__init__()

    def on_data(self, data):
        datajson = json.loads(data)
        if 'retweeted_status' in datajson:
            return
        if datajson['truncated']:
            tweet_text = datajson['extended_tweet']['full_text']
        else:
            tweet_text = datajson['text']
        
        if datajson['geo']:
            location = datajson['geo']
        else:
            location = datajson['user']['location']

        created_at = datajson['created_at']
        userid = datajson['user']['id_str'] 
        followers = datajson['user']['followers_count'] 
        sentiment = self.tweet_analyser(tweet_text)[0]

        subject = self.trace_keyword(tweet_text)
        if not subject:
            return
        print(tweet_text)
        tweet_dict = {"id":userid,"created_at":created_at,"text":tweet_text, "sentiment":sentiment,"location":location,'followers':followers, 'subject':subject}
        self.insert_tweet(tweet_dict)

    def on_error(self, status_code):
        if status_code == 420:
            print('Limit reached, closing stream!')
            time.sleep(5)
            return
        print('Streaming error, status code {})'.format(status_code))
    
    def insert_tweet(self, tweet_dict):
        """insert tweet to mongoDB database

        Attributes
        ----------
        tweet_dict: dict
            dictionary containing tweet elements to be saved to collection
        """
        try:
            tweets_db = self.database
            tweets_db[self.collection].insert_one(tweet_dict)
        except Exception as e:
            print(e)

    def trace_keyword(self, text):
        """check if keyword is present in the tweet text
        
        Attributes
        ----------
        text: str
            text content of the tweet
        """
        for keyword in self.keywords:
            if any(word.upper() in text.upper() for word in keyword.split(' ')):
                return keyword
        return None
