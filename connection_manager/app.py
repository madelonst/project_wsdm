import os
import atexit
from flask import Flask, request, jsonify
from psycopg2 import pool
import string    
import random

db_url = "postgresql://root@lb:26257/defaultdb?sslmode=disable"

pool = pool.SimpleConnectionPool(1, 20, db_url)

app = Flask("connection-manager-service")

def close_db_connection():
    pool.close()
atexit.register(close_db_connection)

@app.post('/exec')
def execute_simple():
    conn = pool.getconn()
    sql = request.json
    result = execute(conn, sql)
    commit(conn)
    return result


@app.post('/start_tx')
def start_transaction():
    conn_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 10))
    conn = pool.getconn(conn_id)
    return conn_id

@app.post('/exec/<conn_id>')
def execute_conn(conn_id: str):
    conn = pool.getconn(conn_id)
    sql = request.json
    return execute(conn, sql)

@app.post('/commit_tx/<conn_id>')
def commit_transaction(conn_id: str):
    conn = pool.getconn(conn_id)
    commit(conn)
    return "Success"

#Helper functions:
def execute(conn, sql):
    cursor = conn.cursor()
    try:
        cursor.execute(sql["sql"], sql["params"])
    except Exception as err:
        return "Error: " + str(err)
    if cursor.description is None:
        result = "Success"
    else:
        result = [dict((cursor.description[i][0], value) \
            for i, value in enumerate(row)) for row in cursor.fetchall()]
    cursor.close()
    return jsonify(result)

def commit(conn):
    conn.commit()
    pool.putconn(conn)
