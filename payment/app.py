import os
import atexit

from flask import Flask

from math import floor
import uuid
import time
import random
import logging
from argparse import ArgumentParser, RawTextHelpFormatter
import psycopg2

app = Flask("payment-service")


db_url = "postgresql://root@cockroach-db:26257/defaultdb?sslmode=disable"
conn = psycopg2.connect(db_url)


user_id_counter = 0
@app.post('/create_user')
def create_user():
    global user_id_counter
    user_id_counter = user_id_counter + 1
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO accounts (user_id, credit) VALUES ({}, 0)".format(user_id_counter))
        logging.debug("create_accounts(): status message: %s",
                      cur.statusmessage)
    conn.commit()
    return {"user_id": user_id_counter}

@app.get('/find_user/<user_id>')
def find_user(user_id: int):
    pass


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
