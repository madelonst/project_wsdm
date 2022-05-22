import os
import atexit

from flask import Flask
# import redis

from math import floor
import uuid
import time
import random
import logging
from argparse import ArgumentParser, RawTextHelpFormatter
import psycopg2


gateway_url = os.environ['GATEWAY_URL']

app = Flask("order-service")

# db: redis.Redis = redis.Redis(host=os.environ['REDIS_HOST'],
#                               port=int(os.environ['REDIS_PORT']),
#                               password=os.environ['REDIS_PASSWORD'],
#                               db=int(os.environ['REDIS_DB']))


db_url = "postgresql://root@cockroach-db:26257/defaultdb?sslmode=disable"
conn = psycopg2.connect(db_url)

with conn.cursor() as cur:
    cur.execute(
        "CREATE TABLE IF NOT EXISTS order_headers (order_id INT PRIMARY KEY, user_id INT, paid BOOLEAN)"
    )
    cur.execute(
        "CREATE TABLE IF NOT EXISTS order_items (order_id INT PRIMARY KEY, item INT, unit_price INT)"
    )
    conn.commit()

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
    return {"this": "is a", "json": "example"}


@app.post('/checkout/<order_id>')
def checkout(order_id):
    pass
