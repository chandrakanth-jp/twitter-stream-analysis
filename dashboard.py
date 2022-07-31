
import streamlit as st
import pymongo
import pandas as pd
from decouple import config 
from stream_tweets import MyStreamListener, auth
import matplotlib.pyplot as plt
import numpy as np
import tweepy
from datetime import datetime
import os, logging, argparse
import time

def connect_to_database():
        """connect to MongoDB database"""
        client=pymongo.MongoClient(config('MONGO_ATLAS'))
        return client

def load_data(client,collection_name):
        """loads records from a collection

        Attributes
        ----------
        client: MongoClient instance
        collection: str
                name of collection
        """
        all_records = list(client['td'][collection_name].find())
        df_norm =  pd.json_normalize(all_records)
        return df_norm


def sentiment_label(df):
        """rename label names for sentiment column

        Attributes
        ----------
        df: MongoDB database instance
        """
        df.loc[df['sentiment.label'] == 'LABEL_0','sentiment.label'] = 'Negative'
        df.loc[df['sentiment.label'] == 'LABEL_1','sentiment.label'] = 'Neutral'
        df.loc[df['sentiment.label'] == 'LABEL_2','sentiment.label'] = 'Positive'
        df.drop('_id', axis=1, inplace=True)
        return (df)

def generate_pie_chart(database, subject):
        """"generate pie chart of sentiment label  for a subject
        
        Attributes
        ----------
        database: MongoDB database instance
        subject: str
                name of subject
        """
        labels = 'Negative', 'Neutral', 'Positive'

        sizes = [database.loc[(database['subject']==subject) & (database['sentiment.label']=='Negative')].shape[0],
                database.loc[(database['subject']==subject) & (database['sentiment.label']=='Neutral')].shape[0],
                database.loc[(database['subject']==subject) & (database['sentiment.label']=='Positive')].shape[0]]

        fig1, ax1 = plt.subplots()
        ax1.pie(sizes, labels=labels, autopct='%1.1f%%', shadow=False, startangle=90)
        ax1.axis('equal')
        return fig1

@st.cache
def get_tweet_count(df, subject):
        """get count of tweets about a subject from dataframe
        
        Attributes
        ----------
        df: dataframe object
        subject: str
                name of the subject from the dataframe
        """
        db = df.loc[(df['subject']==subject)]
        return len(db)

@st.cache
def sentiment_plot_data(df, freq):
        """plots mean sentiment score of subjects against time
        
        Attributes
        ----------
        df: pandas dataframe
        freq: str
                option indicating duration for resampling (H,D,W)
        """
        df.loc[df['sentiment.label']=='Negative', 'sentiment.score'] *= -1
        df.loc[df['sentiment.label']=='Neutral', 'sentiment.score'] = 0
        df['created_at'] = df['created_at'].apply(lambda x: datetime.strptime(x,'%a %b %d %H:%M:%S %z %Y'))
        df_sentiment = df.set_index('created_at').groupby('subject').resample(freq)['sentiment.score'].mean().unstack(level=0, fill_value=0)
        df_sentiment.index.rename('Date', inplace=True)
        df_sentiment = df_sentiment.rename_axis(None, axis='columns')
        return df_sentiment


st.set_page_config(layout="wide")

col1,padding,col2 = st.columns([4,1,4])

mongo_client = connect_to_database()

option = st.sidebar.selectbox(label='Select Collection from database', options=mongo_client['td'].list_collection_names(),
                                index=0)
if option:
        df = load_data(mongo_client, option)
        df = sentiment_label(df)
        last_date = df['created_at'].apply(lambda x: datetime.strptime(x,'%a %b %d %H:%M:%S %z %Y')).max()
        influential=df.sort_values(['followers'], ascending=False)
        col1.subheader('Top Tweets')
        col1.dataframe(influential[['text','followers','subject','location']].head(10).reset_index(drop=True),
                                        width=2000, height=400)
        col1.write('Last download on ' + str(last_date)[:-6] )
        subjects = df.subject.unique() 

        with st.sidebar:
                subject_options = st.sidebar.selectbox(label='Subjects to Include:', options=subjects.tolist())
                with st.form(key='collection'):
                        submit_button = st.form_submit_button(label='Sentiment Analysis')
               
pad1,cont1,pad2 = st.columns((1,2,1))

if submit_button:
        fig = generate_pie_chart(df,subject_options)
        col2.subheader('Sentiment Analysis')
        col2.pyplot(fig)               
        col2.write('Tweet count: ' + str(get_tweet_count(df,subject_options)))
        timeline_plot = sentiment_plot_data(df, 'D')
        cont1.subheader('Sentiment Time Series Plot')
        cont1.line_chart(timeline_plot)

pad_ = st.sidebar.columns(1)

st.sidebar.write('Create a collection')

collection = st.sidebar.text_input(label='Name', value='', max_chars=15)

def user_form_input(database, collection):
        """checks user's input for collection name and generates relevant forms
        
        Attributes
        ----------
        database: MongoDB database 
        collection: str
                name of collection 
        """
        if collection in database.list_collection_names():
                form_prompt_submit(collection)
        else:
                form_submit(collection)

def stream_tweets(collection,duration, search_term):
        """starts a stream based on user inputs
        
        Attributes:
        collection: str
                name of collection
        duration: int
                duration of tweet stream in minutes
        search_term: list 
                list of strings containing keywords 
        """
        database = mongo_client['td']
        if search_term and duration:
                keywords = search_term.split(',')
                myStreamListener = MyStreamListener(keywords, database, collection)
                myStream = tweepy.Stream(auth=auth().auth, listener=myStreamListener)
                myStream.filter(languages=["en"], track=keywords, is_async=True)
                my_bar = st.sidebar.progress(0)
                for i in range(int(100)):
                        time.sleep(duration*0.6)
                        my_bar.progress(i + 1)
                myStream.disconnect()

def form_prompt_submit(collection):
        """creates a form for user when the input collection already exists
        
        Attributes
        ----------
        collection: str
                name of collection
        """
        with st.sidebar:
                search_term = st.text_input(label='Keywords', value='', max_chars=30)
                duration = st.selectbox(label='Duration', options=[1,5,10])
                get_tweets_form = st.form("stream_checkbox_button", clear_on_submit = True)
                with get_tweets_form:
                        agree=st.checkbox('Collection exists, do you want to proceed?')
                        submit = get_tweets_form.form_submit_button("Stream Tweets")
                if agree and submit:
                                stream_tweets(collection,duration,search_term)
                else:
                        return

def form_submit(collection):
        """creates a form for user when input collection is new
        
        Attributes
        ----------
        collection: str
                collection name
        """
        with st.sidebar:
                search_term = st.text_input(label='Keywords', value='', max_chars=30)
                duration = st.selectbox(label='Duration', options=[1,5,10])
                get_tweets_form = st.form("stream_button", clear_on_submit = True)
                with get_tweets_form:
                        submit = get_tweets_form.form_submit_button("Stream Tweets")
                if submit:
                        stream_tweets(collection, duration,search_term)

if collection:
        user_form_input(mongo_client['td'], collection)
