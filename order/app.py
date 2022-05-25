import os
import atexit

import requests
from flask import Flask
import redis
import psycopg2
import random
import requests

gateway_url = os.environ['GATEWAY_URL']

app = Flask("order-service")

db: redis.Redis = redis.Redis(host=os.environ['REDIS_HOST'],
                              port=int(os.environ['REDIS_PORT']),
                              password=os.environ['REDIS_PASSWORD'],
                              db=int(os.environ['REDIS_DB']))

db_url = "postgresql://root@cockroach-db:26257/defaultdb?sslmode=disable"
stock_url = "http://stock-service:5000/"
payment_url = "http://payment-service:5000/"
conn = psycopg2.connect(db_url)

def close_db_connection():
    db.close()


atexit.register(close_db_connection)


# @app.post('/create/<user_id>')
@app.get('/create/<user_id>')
def create_order(user_id):
    order_id = random.randrange(999999999)
    print(str(order_id) + " " + str(user_id), flush=True)

    with conn.cursor() as cur:
        cur.execute("INSERT INTO order_headers (order_id, user_id, paid) VALUES ({},{}, FALSE)".format(order_id, user_id))
    conn.commit()
    return {"order_id": order_id}

# @app.delete('/remove/<order_id>')
@app.get('/remove/<order_id>')
def remove_order(order_id):
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM order_headers WHERE order_id={}".format(order_id))
    conn.commit()
    return "SUCCESS"

# @app.post('/addItem/<order_id>/<item_id>')
@app.get('/addItem/<order_id>/<item_id>')
def add_item(order_id, item_id):

    # Get unit price of item
    response = requests.get(stock_url + "find/" + item_id)
    if response.status_code != 200:
        print("Request to " + stock_url + " failed")
    unit_price = response.json()["price"]
    print("unit_price: " + str(unit_price), flush=True)

    with conn.cursor() as cur:
        cur.execute("INSERT INTO order_items (order_id, item, unit_price) VALUES ({},{},{})".format(order_id, item_id, unit_price))
    conn.commit()
    return "SUCCESS"


# @app.delete('/removeItem/<order_id>/<item_id>')
@app.get('/removeItem/<order_id>/<item_id>')
def remove_item(order_id, item_id):
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM order_items WHERE order_id={} AND item={}".format(order_id, item_id))
    conn.commit()
    print("Removing item: " + str(item_id) + " from order: " + str(order_id) , flush=True)
    return "SUCCESS"

@app.get('/find/<order_id>')
def find_order(order_id):
    items = []
    with conn.cursor() as cur:
        # Get the list of items
        cur.execute(
            "SELECT item FROM order_items WHERE order_id={}".format(order_id))
        rows = cur.fetchall()
        for row in rows:
            items.append(row[0])

        # Get the total cost of the order
        cur.execute(
            "SELECT SUM(unit_price) FROM order_items WHERE order_id={}".format(order_id))
        rows = cur.fetchall()
        total_cost = rows[0][0]

        # Get the user_id and whether an order has been paid for
        cur.execute(
            "SELECT user_id, paid FROM order_headers WHERE order_id={}".format(order_id))
        rows = cur.fetchall()
        user_id = rows[0][0]
        paid = rows[0][1]

    conn.commit()
    return {"order_id": order_id, "paid": paid, "items":items, "user_id": user_id, "total_cost": total_cost}


# @app.post('/checkout/<order_id>')
@app.get('/checkout/<order_id>')
def checkout(order_id):
    # Get the user_id from the corresponding order_id
    with conn.cursor() as cur:
        # Get the user id
        cur.execute(
            "SELECT user_id FROM order_headers WHERE order_id={}".format(order_id))
        rows = cur.fetchall()
        user_id = rows[0][0]

        # Calculate the total amount to pay
        cur.execute(
            "SELECT SUM(unit_price) FROM order_items WHERE order_id={}".format(order_id))
        rows = cur.fetchall()
        total_cost = rows[0][0]
    conn.commit()

    print("User id: " + str(user_id) + " total price: " + str(total_cost))
    response = requests.post(payment_url + "pay/" + str(user_id) + "/" + str(order_id) + "/" + str(total_cost))

    if response.status_code == 200:
        print("Payment succesful", flush=True)
    else:
        print("Payment unsuccesful", flush=True)

    # Substract all the necessary items from stock
    with conn.cursor() as cur:
        cur.execute(
            "SELECT item, count(item) FROM order_items WHERE order_id={} GROUP BY item".format(order_id))
        rows = cur.fetchall()
        for row in rows:
            item_id = row[0]
            amount = row[1]
            response = requests.post(str(stock_url) + "subtract/" + str(item_id) + "/" + str(amount))
            if response.status_code == 200:
                print("Substracted " + str(amount) + " item_id: " + str(item_id) + " from stock", flush=True)
            else:
                print("Substracting stock unsuccesful", flush=True)

    conn.commit()

    return "SUCCESS"



