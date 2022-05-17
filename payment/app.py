import os
import atexit

from flask import Flask
import redis

from math import floor
import os
import random
import uuid

import time
import random
import logging
import os
from argparse import ArgumentParser, RawTextHelpFormatter
import psycopg2

app = Flask("payment-service")

db: redis.Redis = redis.Redis(host=os.environ['REDIS_HOST'],
                              port=int(os.environ['REDIS_PORT']),
                              password=os.environ['REDIS_PASSWORD'],
                              db=int(os.environ['REDIS_DB']))

db_url = "postgresql://root@cockroach-db:26257/defaultdb?sslmode=disable"
conn = psycopg2.connect(db_url)

def close_db_connection():
    db.close()
atexit.register(close_db_connection)

@app.post('/create_user')
def create_user():
    pass

@app.get('/find_user/<user_id>')
def find_user(user_id: int):
    with conn.cursor() as cur:
        cur.execute(
            "CREATE TABLE IF NOT EXISTS accounts (id INT PRIMARY KEY, balance INT)"
        )
        cur.execute(
            "INSERT INTO accounts (id, balance) VALUES ("+user_id+", 1000)")
        logging.debug("create_accounts(): status message: %s",
                      cur.statusmessage)
    conn.commit()
    return {"SUCCESSS????": "hI"}


@app.post('/add_funds/<user_id>/<amount>')
def add_credit(user_id: str, amount: int):
    pass


@app.post('/pay/<user_id>/<order_id>/<amount>')
def remove_credit(user_id: str, order_id: str, amount: int):
    pass


@app.post('/cancel/<user_id>/<order_id>')
def cancel_payment(user_id: str, order_id: str):
    pass


@app.post('/status/<user_id>/<order_id>')
def payment_status(user_id: str, order_id: str):
    pass
