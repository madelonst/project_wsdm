from flask import Flask, request
import requests
import random

import cmi


app = Flask("order-service")

stock_url = "http://stock-service:5000"
payment_url = "http://payment-service:5000"

@app.post('/create/<user_id>')
def create_order(user_id):
    conn_id = request.headers.get("conn_id")
    while True:
        order_id = random.randrange(999999999) #''.join(random.choices(string.ascii_uppercase + string.digits, k = 9))
        response = cmi.exec("INSERT INTO order_headers (order_id, user_id, paid) VALUES (%s,%s, FALSE) RETURNING order_id", [order_id, user_id], conn_id)
        if response.status_code == 200:
            result = response.json()
            if len(result) == 1:
                return result[0], 200

@app.delete('/remove/<order_id>')
def remove_order(order_id):
    conn_id = request.headers.get("conn_id")
    return cmi.get_status("DELETE FROM order_headers WHERE order_id=%s", [order_id], conn_id)

@app.post('/addItem/<order_id>/<item_id>')
def add_item(order_id, item_id):
    conn_id = request.headers.get("conn_id")
    connheaderset = conn_id != None
    if not connheaderset:
        conn_id = cmi.start_tx()

    response = requests.get("{}/find/{}".format(stock_url, item_id), headers={"conn_id": conn_id})
    if response.status_code != 200:
        if not connheaderset:
            cmi.cancel_tx(conn_id)
        return '{"done": false}', 400
    unit_price = response.json()["price"]
    
    response = cmi.get_status("INSERT INTO order_items (order_id, item, unit_price) VALUES (%s,%s,%s)", [order_id, item_id, unit_price], conn_id)

    if not connheaderset:
        cmi.commit_tx(conn_id)

    return response

@app.delete('/removeItem/<order_id>/<item_id>')
def remove_item(order_id, item_id):
    conn_id = request.headers.get("conn_id")
    return cmi.get_status("DELETE FROM order_items WHERE order_id=%s AND item=%s", [order_id, item_id], conn_id)

@app.get('/find/<order_id>')
def find_order(order_id):
    conn_id = request.headers.get("conn_id")
    return cmi.get_one("SELECT order_id, paid, json_agg(item) as items, user_id, SUM(unit_price) as total_cost FROM order_items WHERE order_id=%s", [order_id], conn_id)

@app.post('/checkout/<order_id>')
def checkout(order_id):
    conn_id = request.headers.get("conn_id")
    connheaderset = conn_id != None
    if not connheaderset:
        conn_id = cmi.start_tx()

    response = cmi.get_one("SELECT user_id, SUM(unit_price) as total_cost, json_agg(item) as items FROM order_items WHERE order_id=%s", [order_id], conn_id)
    if response.status_code != 200:
        if not connheaderset:
            cmi.cancel_tx(conn_id)
        return '{"done": false}', 400
    user_id = response["user_id"]
    amount = response["total_cost"]
    items = response["items"]

    response = requests.get("{}/pay/{}/{}/{}".format(payment_url, user_id, order_id, amount), headers={"conn_id": conn_id})
    if response.status_code != 200:
        if not connheaderset:
            cmi.cancel_tx(conn_id)
        return '{"done": false}', 400
    
    for item_id in items:
        response = requests.get("{}/subtract/{}/{}".format(stock_url, item_id, 1), headers={"conn_id": conn_id})
        if response.status_code != 200:
            if not connheaderset:
                cmi.cancel_tx(conn_id)
            return '{"done": false}', 400

    if not connheaderset:
        cmi.commit_tx(conn_id)
    return '{"done": true}', 200
