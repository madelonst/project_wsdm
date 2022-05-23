import os
import atexit

from math import floor
import uuid
import time
import random
import logging
from argparse import ArgumentParser, RawTextHelpFormatter
import psycopg2

db_url = "postgresql://root@cockroach-db:26257/defaultdb?sslmode=disable"
conn = psycopg2.connect(db_url)

with conn.cursor() as cur:
    cur.execute(
        "CREATE TABLE IF NOT EXISTS stock (item_id INT PRIMARY KEY, unit_price INT, stock_qty INT)"
    )
    conn.commit()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS order_headers (order_id INT PRIMARY KEY, user_id INT, paid BOOLEAN)"
    )
    conn.commit()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS order_items (order_id INT PRIMARY KEY, item INT, unit_price INT)"
    )
    conn.commit()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS accounts (user_id INT PRIMARY KEY, credit INT)"
    )
    conn.commit()

conn.close()
