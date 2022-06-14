FROM python:3.10-slim

WORKDIR /home/flask-app

COPY ./requirements.txt .

RUN pip install -r requirements.txt

COPY ./app.py .

EXPOSE 5000