from flask import Flask, request
# import requests
import random
import sys
# from time import strftime

import cmi

app = Flask("stock-service")

# @app.after_request
# def after_request(response):
#     timestamp = strftime('[%Y-%m-%d %H:%M:%S]')
#     print(f'{timestamp} [Flask request] {request.remote_addr} {request.method} {request.scheme} {request.full_path} {response.status}', flush=True)
#     return response

@app.post('/item/create/<price>')
def create_item(price: int):
    conn_id = request.headers.get("conn_id")
    while True:
        item_id = random.randrange(sys.maxsize) #''.join(random.choices(string.ascii_uppercase + string.digits, k = 9))
        response = cmi.exec("INSERT INTO stock (item_id, unit_price, stock_qty) VALUES (%s,%s, 0) RETURNING item_id", [item_id, price], conn_id)
        if response.status_code == 200:
            result = response.json()
            if len(result) == 1:
                return result[0], 200

@app.get('/find/<item_id>')
def find_item(item_id: str):
    conn_id = request.headers.get("conn_id")
    return cmi.get_one("SELECT stock_qty as stock, unit_price as price FROM stock WHERE item_id=%s", [item_id], conn_id)

@app.post('/add/<item_id>/<amount>')
def add_stock(item_id: str, amount: int):
    conn_id = request.headers.get("conn_id")
    return cmi.get_status("UPDATE stock SET stock_qty = stock_qty + %s WHERE item_id=%s AND stock_qty + %s > stock_qty", [amount, item_id, amount], conn_id)

@app.post('/subtract/<item_id>/<amount>')
def remove_stock(item_id: str, amount: int):
    conn_id = request.headers.get("conn_id")
    return cmi.get_status("UPDATE stock SET stock_qty = stock_qty - %s WHERE item_id=%s AND stock_qty - %s >= 0", [amount, item_id, amount], conn_id)
