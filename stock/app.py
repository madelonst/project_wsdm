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


app = Flask("stock-service")


db_url = "postgresql://root@cockroach-db:26257/defaultdb?sslmode=disable"
conn = psycopg2.connect(db_url)

item_id_counter = 0

@app.post('/item/create/<price>')
def create_item(price: int):
    global item_id_counter
    item_id_counter = item_id_counter + 1
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO stock (item_id, unit_price, stock_qty) VALUES ({},{}, 0)".format(item_id_counter, price))
        logging.debug("create_item(): status message: %s",
                      cur.statusmessage)
    conn.commit()
    return {"item_id": item_id_counter}


@app.get('/find/<item_id>')
def find_item(item_id: str):
    stock_qty = 0
    unit_price = 0
    with conn.cursor() as cur:
        cur.execute(
            "SELECT stock_qty, unit_price FROM stock WHERE item_id={}".format(item_id))
        rows = cur.fetchall()
        for row in rows:
            stock_qty = row[0]
            unit_price = row[1]
    return {"stock": stock_qty, "price": unit_price}


@app.post('/add/<item_id>/<amount>')
def add_stock(item_id: str, amount: int):
    new_amount = 0
    with conn.cursor() as cur:
        cur.execute(
            "SELECT stock_qty FROM stock WHERE item_id={}".format(item_id))
        rows = cur.fetchall()
        for row_val in rows:
            new_amount = int(row_val[0]) + int(amount)
        cur.execute(
            "UPDATE stock SET stock_qty = {} WHERE item_id={}".format(new_amount, item_id))
        logging.debug("create_item(): status message: %s",
                      cur.statusmessage)
    conn.commit()
    return "Success", 200


@app.post('/subtract/<item_id>/<amount>')
def remove_stock(item_id: str, amount: int):
    new_amount = 0
    with conn.cursor() as cur:
        cur.execute(
            "SELECT stock_qty FROM stock WHERE item_id={}".format(item_id))
        rows = cur.fetchall()
        for row_val in rows:
            new_amount = int(row_val[0]) - int(amount)

        cur.execute(
            "UPDATE stock SET stock_qty = {} WHERE item_id={}".format(new_amount, item_id))
        logging.debug("create_item(): status message: %s",
                      cur.statusmessage)
    conn.commit()
    return "Success", 200
