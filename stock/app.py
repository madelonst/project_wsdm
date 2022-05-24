from flask import Flask

from math import floor
import random
import cmi

app = Flask("stock-service")

@app.post('/item/create/<price>')
def create_item(price: int):
    while True:
        item_id = random.randrange(999999999) #''.join(random.choices(string.ascii_uppercase + string.digits, k = 9))
        response = cmi.exec("INSERT INTO stock (item_id, unit_price, stock_qty) VALUES (%s,%s, 0) RETURNING item_id", [item_id, price])
        if response.status_code == 200:
            result = response.json()
            if len(result) == 1:
                return result[0], 200
    return '{"status": "Error"}'

@app.get('/find/<item_id>')
def find_item(item_id: str):
    return cmi.get_one("SELECT stock_qty, unit_price FROM stock WHERE item_id=%s", [item_id])

@app.post('/add/<item_id>/<amount>')
def add_stock(item_id: str, amount: int):
    return cmi.get_status("UPDATE stock SET stock_qty = stock_qty + %s WHERE item_id=%s AND stock_qty + %s > stock_qty", [amount, item_id, amount])


@app.post('/subtract/<item_id>/<amount>')
def remove_stock(item_id: str, amount: int):
    return cmi.get_status("UPDATE stock SET stock_qty = stock_qty - %s WHERE item_id=%s AND stock_qty - %s >= 0", [amount, item_id, amount])
