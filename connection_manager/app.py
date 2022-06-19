import atexit
from flask import Flask, request, jsonify
from psycopg2 import pool
import string
import random
import os
# from time import strftime

db_url = "postgresql://root@cockroachdb-public:26257/defaultdb?sslmode=disable"

ip = os.getenv('MY_POD_IP')

pool = pool.SimpleConnectionPool(1, 100, db_url)

app = Flask("connection-manager-service")

def close_db_connection():
    pool.closeall()
atexit.register(close_db_connection)

# @app.after_request
# def after_request(response):
#     timestamp = strftime('[%Y-%m-%d %H:%M:%S]')
#     print(f'{timestamp} [Flask request] {request.remote_addr} {request.method} {request.scheme} {request.full_path} {response.status}', flush=True)
#     return response

@app.post('/exec')
def execute_simple():
    conn = pool.getconn()
    sql = request.json
    result = execute(conn, sql)
    commit(conn)
    return result

@app.get('/start_tx')
def start_transaction():
    conn_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 10))
    conn = pool.getconn(conn_id)
    return f"{ip}:{conn_id}", 200

@app.post('/get_success/<conn_id>')
def get_success(conn_id: str):
    try:
        conn = pool.getconn(conn_id)
    except Exception:
        return "", 400
    
    cursor = conn.cursor()
    body = request.json

    try:
        cursor.execute(body["sql"], body["params"])
    except Exception as err:
        cursor.close()
        conn.rollback()
        conn.close()
        return "", 400
    cursor.close()
    conn.commit()
    conn.close()
    return "", 200

@app.post('/get_one/<conn_id>')
def get_one(conn_id: str):
    try:
        conn = pool.getconn(conn_id)
    except Exception:
        return result, 200

    cursor = conn.cursor()
    body = request.json

    try:
        cursor.execute(body["sql"], body["params"])
    except Exception as err:
        cursor.close()
        conn.rollback()
        conn.close()
        return "", 400
    result = dict((cursor.description[i][0], value) for i, value in enumerate(cursor.fetchone()))
    cursor.close()
    conn.commit()
    conn.close()
    return result, 200

@app.post('/get_single/<conn_id>')
def get_single(conn_id: str):
    try:
        conn = pool.getconn(conn_id)
    except Exception:
        return result, 200

    cursor = conn.cursor()
    body = request.json

    try:
        cursor.execute(body["sql"], body["params"])
    except Exception as err:
        cursor.close()
        conn.rollback()
        conn.close()
        return "", 400
    result = cursor.fetchone()[0]
    cursor.close()
    conn.commit()
    conn.close()
    return result, 200

@app.post('/exec/<conn_id>')
def execute_conn(conn_id: str):
    conn = pool.getconn(conn_id)
    sql = request.json
    result = execute(conn, sql)
    pool.putconn(conn)
    return result

@app.post('/commit_tx/<conn_id>')
def commit_transaction(conn_id: str):
    conn = pool.getconn(conn_id)
    commit(conn)
    return "Success", 200

@app.post('/cancel_tx/<conn_id>')
def cancel_transaction(conn_id: str):
    conn = pool.getconn(conn_id)
    conn.rollback()
    conn.close()
    pool.putconn(conn)
    return "Success", 200


#Helper functions:
def execute(conn, sql):
    cursor = conn.cursor()
    try:
        cursor.execute(sql["sql"], sql["params"])
    except Exception as err:
        return "Error: " + str(err), 500
    if cursor.description is None:
        result = cursor.fetchall()
    else:
        result = [dict((cursor.description[i][0], value) \
            for i, value in enumerate(row)) for row in cursor.fetchall()]
    cursor.close()
    return jsonify(result), 200

def commit(conn, conn_id = None):
    conn.commit()
    conn.close()
    pool.putconn(conn)
