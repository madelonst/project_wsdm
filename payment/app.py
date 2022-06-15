from flask import Flask, request
import requests
import random
import re
import sys
# from time import strftime

import cmi

app = Flask("payment-service")

# @app.after_request
# def after_request(response):
#     timestamp = strftime('[%Y-%m-%d %H:%M:%S]')
#     print(f'{timestamp} [Flask request] {request.remote_addr} {request.method} {request.scheme} {request.full_path} {response.status}', flush=True)
#     return response

@app.post('/create_user')
def create_user():
    conn_id = request.headers.get("conn_id")
    while True:
        user_id = random.randrange(sys.maxsize) #''.join(random.choices(string.ascii_uppercase + string.digits, k = 9))
        response = cmi.exec("INSERT INTO accounts (user_id, credit) VALUES (%s, 0) RETURNING user_id", [user_id], conn_id)
        if response.status_code == 200:
            result = response.json()
            if len(result) == 1:
                return result[0], 200

@app.get('/find_user/<user_id>')
def find_user(user_id: int):
    conn_id = request.headers.get("conn_id")
    res, status = cmi.get_one("SELECT user_id, credit FROM accounts WHERE user_id=%s", [user_id], conn_id)
    if status == 200:
        res["credit"] = float(res["credit"])
    return res, status

@app.post('/add_funds/<user_id>/<amount>')
def add_credit(user_id: str, amount: int):
    conn_id = request.headers.get("conn_id")
    return cmi.get_status("UPDATE accounts SET credit = credit + %s WHERE user_id=%s AND credit + %s > credit",
                          [amount, user_id, amount], conn_id)

@app.post('/pay/<user_id>/<order_id>/<amount>')
def remove_credit(user_id: str, order_id: str, amount: int):
    conn_id = request.headers.get("conn_id")
    connheaderset = conn_id != None
    if not connheaderset:
        conn_id = cmi.start_tx()

    _, status_code = cmi.get_status("UPDATE accounts SET credit = credit - CAST(%s AS NUMERIC) WHERE user_id=%s AND credit - CAST(%s AS NUMERIC) >= 0 AND CAST(%s AS NUMERIC) > 0",
                          [amount, user_id, amount, amount], conn_id)
    if status_code != 200:
        if not connheaderset:
            cmi.cancel_tx(conn_id)
        return '{"done": false}', 400
    
    _, status_code = cmi.get_status("UPDATE order_headers SET paid = TRUE WHERE order_id=%s AND user_id=%s AND paid = FALSE", [order_id, user_id], conn_id)
    if status_code != 200:
        if not connheaderset:
            cmi.cancel_tx(conn_id)
        return '{"done": false}', 400

    if not connheaderset:
        cmi.commit_tx(conn_id)
    return '{"done": true}', 200

@app.post('/cancel/<user_id>/<order_id>')
def cancel_payment(user_id: str, order_id: str):
    conn_id = request.headers.get("conn_id")
    connheaderset = conn_id != None
    if not connheaderset:
        conn_id = cmi.start_tx()

    _, status_code = cmi.get_status("UPDATE accounts SET credit = credit + CAST((SELECT SUM(unit_price) FROM order_items WHERE order_id=%s) AS INTEGER) WHERE user_id=%s",
                              [order_id, user_id], conn_id)
    if status_code != 200:
        if not connheaderset:
            cmi.cancel_tx(conn_id)
        return '{"done": false}', 400
    
    _, status_code = cmi.get_status("UPDATE order_headers SET paid = FALSE WHERE order_id=%s", [order_id], conn_id)
    if status_code != 200:
        if not connheaderset:
            cmi.cancel_tx(conn_id)
        return '{"done": false}', 400

    if not connheaderset:
        cmi.commit_tx(conn_id)
    return '{"done": true}', 200

#Changed to GET based on project document
@app.get('/status/<user_id>/<order_id>')
def payment_status(user_id: str, order_id: str):
    conn_id = request.headers.get("conn_id")
    return cmi.get_one("SELECT paid FROM order_headers WHERE order_id=%s", [order_id], conn_id)
