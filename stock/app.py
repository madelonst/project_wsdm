from psycogreen.gevent import patch_psycopg
patch_psycopg()
from gevent import monkey
monkey.patch_all()

from flask import Flask, request, g
# import requests
import random
# from time import strftime

import cmi

app = Flask("stock-service")

@app.before_request
def before_request():
    g.cmstr = request.headers.get("cm")
    if g.cmstr != None:
        g.already_using_connection_manager = True
        g.cm = tuple(g.cmstr.split(':'))
    else:
        g.already_using_connection_manager = False
        g.cm = None

# @app.after_request
# def after_request(response):
#     timestamp = strftime('[%Y-%m-%d %H:%M:%S]')
#     print(f'{timestamp} [Flask request] {request.remote_addr} {request.method} {request.scheme} {request.full_path} {response.status}', flush=True)
#     return response

@app.post('/item/create/<price>')
def create_item(price: int):
    while True:
        item_id = random.randrange(0, 9223372036854775807) #Cockroachdb max and min INT values (64-bit)
        response = cmi.exec("INSERT INTO stock (item_id, unit_price, stock_qty) VALUES (%s,%s, 0) RETURNING item_id",
            [item_id, price], g.cm)
        if response.status_code == 200:
            result = response.json()
            if len(result) == 1:
                return result[0], 200

@app.get('/find/<item_id>')
def find_item(item_id: str):
    return cmi.get_one("SELECT stock_qty as stock, unit_price as price FROM stock WHERE item_id=%s",
        [item_id], g.cm)

@app.post('/add/<item_id>/<amount>')
def add_stock(item_id: str, amount: int):
    return cmi.get_status("UPDATE stock SET stock_qty = stock_qty + %s WHERE item_id=%s AND stock_qty + %s > stock_qty",
        [amount, item_id, amount], g.cm)

@app.post('/subtract/<item_id>/<amount>')
def remove_stock(item_id: str, amount: int):
    return cmi.get_status("UPDATE stock SET stock_qty = stock_qty - %s WHERE item_id=%s AND stock_qty - %s >= 0",
        [amount, item_id, amount], g.cm)
