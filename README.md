# twitter-stream-analysis
Streamlit based app for collecting real-time tweets using Twitter API and gain insights through AI-powered sentiment analysis.


![Streamlit dashboard](/images/streamlit_dashboard.PNG)

## Components
The main components of this project include:
- Tweepy library
- Hugging Face Transformers library (we use the RoBERTa model, a transformer based pre-trained network, finetuned for sentiment analysis)
- MongoDB Atlas
- Streamlit
- Docker

## Prerequisites
- MongoDB Atlas account and connection string https://www.mongodb.com/cloud/atlas/register
- Twitter API key https://developer.twitter.com/en/docs/twitter-api
- Docker 

## Installation
1. Clone the repo
```
git clone https://github.com/chandrakanth-jp/twitter-stream-analysis.git
```
2. Configure .env file with MongoDB connection string and Twitter API key and token.

4. Build docker image, go to the folder and do
```
docker build -t <image_name:tag>
```
4. Run container
```
docker run -it --rm -p 8501:8501 <image_name:tag>
```
