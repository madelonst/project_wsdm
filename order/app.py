from flask import Flask, request, g
import requests
import random
# from time import strftime

import cmi
import qi

app = Flask("order-service")

stock_url = "http://stock-service:5000"
payment_url = "http://payment-service:5000"

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

@app.post('/create/<user_id>')
def create_order(user_id):
    while True:
        order_id = random.randrange(-9223372036854775807, 9223372036854775807) #Cockroachdb max and min INT values (64-bit)
        success = qi.get_success("INSERT INTO order_headers (order_id, user_id, paid) VALUES (%s,%s,FALSE)", [order_id, user_id], g.cm)
        if success:
            return {"order_id": order_id}, 200
        return "", 400

@app.delete('/remove/<order_id>')
def remove_order(order_id):
    if not g.already_using_connection_manager:
        g.cmstr = cmi.start_tx()
        g.cm = tuple(g.cmstr.split(':'))

    success = cmi.get_success("DELETE FROM order_items WHERE order_id=%s", [order_id], g.cm)
    if not success:
        if not g.already_using_connection_manager:
            cmi.cancel_tx(g.cm)
        return '{"done": false}', 400

    success = cmi.get_success("DELETE FROM order_headers WHERE order_id=%s", [order_id], g.cm)
    if not success:
        if not g.already_using_connection_manager:
            cmi.cancel_tx(g.cm)
        return '{"done": false}', 400

    if not g.already_using_connection_manager:
        cmi.commit_tx(g.cm)
    return '{"done": true}', 200

@app.post('/addItem/<order_id>/<item_id>')
def add_item(order_id, item_id):
    return qi.get_done("INSERT INTO order_items (order_id, item_id, count) VALUES (%s,%s,1) ON CONFLICT (order_id, item_id) DO UPDATE SET count = order_items.count+1", [order_id, item_id], g.cm)

@app.delete('/removeItem/<order_id>/<item_id>')
def remove_item(order_id, item_id):
    if not g.already_using_connection_manager:
        g.cmstr = cmi.start_tx()
        g.cm = tuple(g.cmstr.split(':'))

    data, status_code = cmi.get_one("UPDATE order_items SET count=count-1 WHERE order_id=%s AND item_id=%s RETURNING count", [order_id, item_id], g.cm)
    if status_code != 200:
        if not g.already_using_connection_manager:
            cmi.cancel_tx(g.cm)
        print(data, flush=True)
        return '{"done": false}', 400
    count = data["count"]

    if count == 0:
        success = cmi.get_success("DELETE FROM order_items WHERE order_id=%s AND item_id=%s", [order_id, item_id], g.cm)
        if not success:
            if not g.already_using_connection_manager:
                cmi.cancel_tx(g.cm)
            return '{"done": false}', 400

    if not g.already_using_connection_manager:
        cmi.commit_tx(g.cm)
    return '{"done": true}', 200

@app.get('/find/<order_id>')
def find_order(order_id):
    return qi.get_one("SELECT %s AS order_id, (SELECT paid FROM order_headers WHERE order_id=%s) AS paid, coalesce(json_object_agg(item_id::string, count), '{}'::json) AS items, (SELECT user_id FROM order_headers WHERE order_id=%s) AS user_id FROM order_items WHERE order_id=%s;", [order_id, order_id, order_id, order_id], g.cm)

@app.post('/checkout/<order_id>')
def checkout(order_id):
    return '', 400
    if not g.already_using_connection_manager:
        g.cmstr = cmi.start_tx()
        g.cm = tuple(g.cmstr.split(':'))

    user_id, status_code = cmi.get_single("SELECT user_id FROM order_headers WHERE order_id=%s", [order_id], g.cm)
    if status_code != 200:
        if not g.already_using_connection_manager:
            cmi.cancel_tx(g.cm)
        return '{"done": false}', 400

    data, status_code = cmi.get_one("SELECT coalesce(json_object_agg(item_id::string, count), '{}'::json) AS items FROM order_items WHERE order_id=%s", [order_id], g.cm)
    if status_code != 200:
        if not g.already_using_connection_manager:
            cmi.cancel_tx(g.cm)
        return '{"done": false}', 400
    items = data["items"]

    amount = 0
    
    for item_id, count in items.items():
        response = requests.get(f"{stock_url}/find/{item_id}", headers={"cm": ':'.join(g.cm)})
        if response.status_code != 200:
            if not g.already_using_connection_manager:
                cmi.cancel_tx(g.cm)
            return '{"done": false}', 400
        amount += float(response.json()["price"]) * count
        print(amount)

        response = requests.post(f"{stock_url}/subtract/{item_id}/{count}", headers={"cm": ':'.join(g.cm)})
        if response.status_code != 200:
            if not g.already_using_connection_manager:
                cmi.cancel_tx(g.cm)
            return '{"done": false}', 400

    response = requests.post(f"{payment_url}/pay/{user_id}/{order_id}/{amount}", headers={"cm": ':'.join(g.cm)})
    if response.status_code != 200:
        if not g.already_using_connection_manager:
            cmi.cancel_tx(g.cm)
        return '{"done": false}', 400

    if not g.already_using_connection_manager:
        cmi.commit_tx(g.cm)
    return '{"done": true}', 200
