FROM python:3.10-slim

WORKDIR /home/flask-app

COPY ./requirements.txt .

RUN pip install -r requirements.txt

COPY ./app.py .
COPY ./qi.py .
COPY ./cri.py .
COPY ./cmi.py .

EXPOSE 5000