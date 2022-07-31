FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . /app

EXPOSE 8501
 
CMD streamlit run dashboard.py
