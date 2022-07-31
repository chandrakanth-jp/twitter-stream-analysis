FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . /app

#RUN mkdir ~/.streamlit

#RUN cp config.toml ~/.streamlit/config.toml

EXPOSE 8501
 
CMD streamlit run dashboard.py