from flask import Flask, request, g, Response
import requests
import random
from time import strftime

import cmi

app = Flask("order-service")

stock_url = "http://stock-service:5000"
payment_url = "http://payment-service:5000"

@app.before_request
def before_request():
    timestamp = strftime('[%Y-%m-%d %H:%M:%S]')
    print(f'{timestamp} [Flask start request] {request.remote_addr} {request.method} {request.scheme} {request.full_path}', flush=True)
    g.cmstr = request.headers.get("cm")
    if g.cmstr != None:
        g.already_using_connection_manager = True
        g.cm = tuple(g.cmstr.split(':'))
    else:
        g.already_using_connection_manager = False
        g.cm = None

@app.after_request
def after_request(response):
    timestamp = strftime('[%Y-%m-%d %H:%M:%S]')
    print(f'{timestamp} [Flask finish request] {request.remote_addr} {request.method} {request.scheme} {request.full_path} {response.status}', flush=True)
    return response

@app.post('/create/<user_id>')
def create_order(user_id):
    while True:
        order_id = random.randrange(0, 9223372036854775807) #Cockroachdb max and min INT values (64-bit)
        response = cmi.exec("INSERT INTO order_headers (order_id, user_id, paid, total_cost) VALUES (%s,%s,FALSE,0) RETURNING order_id", [order_id, user_id], g.cm)
        if response.status_code == 200:
            result = response.json()
            if len(result) == 1:
                return result[0], 200

@app.delete('/remove/<order_id>')
def remove_order(order_id):
    if not g.already_using_connection_manager:
        g.cmstr = cmi.start_tx()
        g.cm = tuple(g.cmstr.split(':'))

    _, status_code = cmi.get_status("DELETE FROM order_items WHERE order_id=%s", [order_id], g.cm)
    if status_code != 200:
        if not g.already_using_connection_manager:
            cmi.cancel_tx(g.cm)
        return 

    _, status_code = cmi.get_status("DELETE FROM order_headers WHERE order_id=%s", [order_id], g.cm)
    if status_code != 200:
        if not g.already_using_connection_manager:
            cmi.cancel_tx(g.cm)
        return cmi.DONE_FALSE

    if not g.already_using_connection_manager:
        cmi.commit_tx(g.cm)
    return '{"done": true}', 200

@app.post('/addItem/<order_id>/<item_id>')
def add_item(order_id, item_id):
    if not g.already_using_connection_manager:
        g.cmstr = cmi.start_tx()
        g.cm = tuple(g.cmstr.split(':'))

    data, status_code = cmi.get_status("INSERT INTO order_items (order_id, item_id, count) VALUES (%s,%s,1) ON CONFLICT (order_id, item_id) DO UPDATE SET count = order_items.count+1",
        [order_id, item_id], g.cm)
    if status_code != 200:
        if not g.already_using_connection_manager:
            cmi.cancel_tx(g.cm)
        return cmi.DONE_FALSE

    response = requests.get(f"{stock_url}/find/{item_id}", headers={"cm": g.cmstr})
    if response.status_code != 200:
        if not g.already_using_connection_manager:
            cmi.cancel_tx(g.cm)
        return cmi.DONE_FALSE
    price = response.json()["price"]

    data, status_code = cmi.get_status("UPDATE order_headers SET total_cost=total_cost+%s WHERE order_id=%s",
        [price, order_id], g.cm)
    if status_code != 200:
        if not g.already_using_connection_manager:
            cmi.cancel_tx(g.cm)
        return cmi.DONE_FALSE
    
    if not g.already_using_connection_manager:
        cmi.commit_tx(g.cm)
    return '{"done": true}', 200

@app.delete('/removeItem/<order_id>/<item_id>')
def remove_item(order_id, item_id):
    if not g.already_using_connection_manager:
        g.cmstr = cmi.start_tx()
        g.cm = tuple(g.cmstr.split(':'))

    print(strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "STARTING QUERY 1", flush=True)
    data, status_code = cmi.get_one("UPDATE order_items SET count=count-1 WHERE order_id=%s AND item_id=%s RETURNING count",
        [order_id, item_id], g.cm)
    print(strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "FINISHED QUERY 1", flush=True)
    if status_code != 200:
        if not g.already_using_connection_manager:
            print(strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "CANCELLING TX 1", flush=True)
            cmi.cancel_tx(g.cm)
            print(strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "CANCELLED TX 1", flush=True)
        return cmi.DONE_FALSE
    if data["count"] == 0:
        cmi.exec("DELETE FROM order_items WHERE order_id=%s AND item_id=%s",
            [order_id, item_id], g.cm)

    print(strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "CALLING STOCK FIND", item_id, flush=True)
    response = requests.get(f"{stock_url}/find/{item_id}", headers={"cm": g.cmstr})
    print(strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "CALLED STOCK FIND", item_id, flush=True)
    if response.status_code != 200:
        if not g.already_using_connection_manager:
            print(strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "CANCELLING TX", flush=True)
            cmi.cancel_tx(g.cm)
            print(strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "CANCELLED TX", flush=True)
        return cmi.DONE_FALSE
    price = response.json()["price"]

    print(strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "STARTING QUERY 2", flush=True)
    data, status_code = cmi.get_status("UPDATE order_headers SET total_cost=total_cost-%s WHERE order_id=%s",
        [price, order_id], g.cm)
    print(strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "FINISHED QUERY 2", flush=True)
    if status_code != 200:
        if not g.already_using_connection_manager:
            print(strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "CANCELLING TX 2", flush=True)
            cmi.cancel_tx(g.cm)
            print(strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "CANCELLED TX 2", flush=True)
        return cmi.DONE_FALSE

    print(strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "COMMITING", flush=True)

    if not g.already_using_connection_manager:
        print(strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "COMMITTING TX", flush=True)
        cmi.commit_tx(g.cm)
        print(strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "COMMITTED TX", flush=True)
    return '{"done": true}', 200

@app.get('/find/<order_id>')
def find_order(order_id):
    return cmi.get_one("SELECT %s AS order_id, (SELECT paid FROM order_headers WHERE order_id=%s) AS paid, coalesce(json_object_agg(item_id::string, count), '{}'::json) AS items, (SELECT user_id FROM order_headers WHERE order_id=%s) AS user_id, (SELECT total_cost FROM order_headers WHERE order_id=%s) AS total_cost FROM order_items WHERE order_id=%s",
        [order_id, order_id, order_id, order_id], g.cm)

@app.post('/checkout/<order_id>')
def checkout(order_id):
    if not g.already_using_connection_manager:
        print(strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "STARTING TX", flush=True)
        g.cmstr = cmi.start_tx()
        print(strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "STARTED TX", flush=True)
        g.cm = tuple(g.cmstr.split(':'))

    print(strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "STARTING QUERY 1", flush=True)
    data, status_code = cmi.get_one("SELECT user_id, total_cost FROM order_headers WHERE order_id=%s",
        [order_id], g.cm)
    print(strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "FINISHED QUERY 1", flush=True)
    if status_code != 200:
        if not g.already_using_connection_manager:
            print(strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "CANCELLING TX 1", flush=True)
            cmi.cancel_tx(g.cm)
            print(strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "CANCELLED TX 1", flush=True)
        return cmi.DONE_FALSE
    user_id = data["user_id"]
    total_price = data["total_cost"]
    print(total_price, flush=True)

    print(strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "CALLING PAYMENT", order_id, flush=True)
    response = requests.post(f"{payment_url}/pay/{user_id}/{order_id}/{total_price}", headers={"cm": g.cmstr})
    print(strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "CALLED PAYMENT", order_id, flush=True)
    if response.status_code != 200:
        if not g.already_using_connection_manager:
            print(strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "CANCELLING TX 3", flush=True)
            cmi.cancel_tx(g.cm)
            print(strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "CANCELLED TX 3", flush=True)
        return cmi.DONE_FALSE

    print(strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "STARTING QUERY 2", flush=True)
    data, status_code = cmi.get_one("SELECT coalesce(json_object_agg(item_id::string, count), '{}'::json) AS items FROM order_items WHERE order_id=%s",
        [order_id], g.cm)
    print(strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "FINISHED QUERY 2", flush=True)
    if status_code != 200:
        if not g.already_using_connection_manager:
            print(strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "CANCELLING TX 2", flush=True)
            cmi.cancel_tx(g.cm)
            print(strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "CANCELLED TX 2", flush=True)
        return cmi.DONE_FALSE
    items = data["items"]
    
    for item_id, count in items.items():
        print(strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "CALLING STOCK SUBTRACT", item_id, flush=True)
        response = requests.post(f"{stock_url}/subtract/{item_id}/{count}", headers={"cm": g.cmstr})
        print(strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "CALLED STOCK SUBTRACT", item_id, flush=True)
        if response.status_code != 200:
            if not g.already_using_connection_manager:
                print(strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "CANCELLING TX", flush=True)
                cmi.cancel_tx(g.cm)
                print(strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "CANCELLED TX", flush=True)
            return cmi.DONE_FALSE

    if not g.already_using_connection_manager:
        print(strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "COMMITTING TX", flush=True)
        cmi.commit_tx(g.cm)
        print(strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], "COMMITTED TX", flush=True)
    return '{"done": true}', 200
