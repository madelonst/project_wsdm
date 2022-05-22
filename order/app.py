import os
import atexit

from flask import Flask
import redis

from json import dumps
from kafka import KafkaProducer

import logging

gateway_url = os.environ['GATEWAY_URL']

app = Flask("order-service")

db: redis.Redis = redis.Redis(host=os.environ['REDIS_HOST'],
                              port=int(os.environ['REDIS_PORT']),
                              password=os.environ['REDIS_PASSWORD'],
                              db=int(os.environ['REDIS_DB']))

producer = KafkaProducer(
    bootstrap_servers=['kafka:9093'],
    api_version=(0,11,5),
    value_serializer=lambda x: dumps(x).encode('utf-8')
)

def close_db_connection():
    db.close()


atexit.register(close_db_connection)


@app.post('/create/<user_id>')
def create_order(user_id):
    pass


@app.delete('/remove/<order_id>')
def remove_order(order_id):
    pass


@app.post('/addItem/<order_id>/<item_id>')
def add_item(order_id, item_id):
    pass


@app.delete('/removeItem/<order_id>/<item_id>')
def remove_item(order_id, item_id):
    pass


@app.get('/find/<order_id>')
def find_order(order_id):
    logging.debug("test")
    data = {'counter': order_id}
    producer.send('topic_test', value=data)
        # sleep(0.5)
    return data


@app.post('/checkout/<order_id>')
def checkout(order_id):
    pass
