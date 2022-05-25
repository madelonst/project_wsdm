from flask import Flask, request

from math import floor
import random
import cmi

app = Flask("payment-service")



@app.post('/create_user')
def create_user():
    while True:
        user_id = random.randrange(999999999) #''.join(random.choices(string.ascii_uppercase + string.digits, k = 9))
        response = cmi.exec("INSERT INTO accounts (user_id, credit) VALUES (%s, 0) RETURNING user_id", [user_id])
        if response.status_code == 200:
            result = response.json()
            if len(result) == 1:
                return result[0], 200
    return '{"status": "Error"}'


@app.get('/find_user/<user_id>')
def find_user(user_id: int):
    return cmi.get_one("SELECT user_id, credit FROM accounts WHERE user_id=%s", [user_id])


@app.post('/add_funds/<user_id>/<amount>')
def add_credit(user_id: str, amount: int):
    return cmi.get_status("UPDATE accounts SET credit = credit + %s WHERE user_id=%s AND credit + %s > credit",
                          [amount, user_id, amount])


@app.post('/pay/<user_id>/<order_id>/<amount>')
def remove_credit(user_id: str, order_id: str, amount: int):
    response = cmi.get_status("UPDATE accounts SET credit = credit - %s WHERE user_id=%s AND credit - %s >= 0",
                          [amount, user_id, amount])
    if response.status_code == 200:
        return cmi.get_status("UPDATE order_headers SET paid = TRUE WHERE order_id=%s", [order_id])
    else:
        return response


@app.post('/cancel/<user_id>/<order_id>')
def cancel_payment(user_id: str, order_id: str):
    response = cmi.get_status("UPDATE accounts SET credit = credit + (SELECT SUM(unit_price) FROM order_items WHERE order_id=%s) WHERE user_id=%s",
                              [order_id, user_id])
    if response.status_code == 200:
        return cmi.get_status("UPDATE order_headers SET paid = FALSE WHERE order_id=%s", [order_id])
    return reponse

#Changed to GET based on project document
@app.get('/status/<user_id>/<order_id>')
def payment_status(user_id: str, order_id: str):
    return cmi.get_one("SELECT paid FROM order_headers WHERE order_id=%s", [order_id])
