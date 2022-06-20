from psycogreen.gevent import patch_psycopg
patch_psycopg()
from gevent import monkey
monkey.patch_all()

import atexit
from flask import Flask, request, jsonify
from psycopg2 import pool
from psycopg2.errors import SerializationFailure
import string
import random
import os
from time import sleep #strftime

db_url = "postgresql://root@cockroachdb-public:26257/defaultdb?sslmode=disable"

max_retries = 9999999999

ip = os.getenv('MY_POD_IP')

pool = pool.SimpleConnectionPool(1, 200, db_url)

conns = {}

app = Flask("connection-manager-service")

def close_db_connection():
    pool.closeall()
atexit.register(close_db_connection)

# @app.before_request
# def after_request():
#     timestamp = strftime('[%Y-%m-%d %H:%M:%S]')
#     print(f'{timestamp} [Flask start request] {request.remote_addr} {request.method} {request.scheme} {request.full_path}', flush=True)

# @app.after_request
# def after_request(response):
#     timestamp = strftime('[%Y-%m-%d %H:%M:%S]')
#     print(f'{timestamp} [Flask end request] {request.remote_addr} {request.method} {request.scheme} {request.full_path} {response.status}', flush=True)
#     return response

@app.get('/start_tx')
def start_transaction():
    conn_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 10))
    conn = pool.getconn()
    conns[conn_id] = (conn, [])
    return f"{ip}:{conn_id}", 200

@app.post('/exec/<conn_id>')
def execute_conn(conn_id: str):
    conn, queries = conns[conn_id]
    sql = request.json
    print(sql, flush=True)
    result = execute(conn, sql, queries)
    queries.append(sql)
    print(result, flush=True)
    return result

@app.post('/commit_tx/<conn_id>')
def commit_transaction(conn_id: str):
    conn = conns[conn_id][0]
    conn.commit()
    conn.close()
    del conns[conn_id]
    pool.putconn(conn)
    return "Success", 200

@app.post('/cancel_tx/<conn_id>')
def cancel_transaction(conn_id: str):
    conn = conns[conn_id][0]
    conn.rollback()
    conn.close()
    del conns[conn_id]
    pool.putconn(conn)
    return "Success", 200


#Helper functions:
def execute(conn, sql, queries):
    cursor = conn.cursor()
    for retry in range(1, max_retries + 1):
        try:
            if retry != 1:
                print("WOW, WE LOOPED", flush=True)
                for q in queries:
                    cursor.execute(q["sql"], q["params"])
            cursor.execute(sql["sql"], sql["params"])
            break
        except SerializationFailure as e:
            # This is a retry error, so we roll back the current
            # transaction and sleep for a bit before retrying. The
            # sleep time increases for each failed transaction.
            conn.rollback()
            sleep_ms = (2**retry) * 0.1 * (random.random() + 0.5)
            sleep(sleep_ms)
            print("LOOPING DUE TO CLIENT RETRY", flush=True)

        except Exception as err:

            return "Error: " + str(err), 500

    if cursor.description is None:
        result = cursor.fetchall()
    else:
        result = [dict((cursor.description[i][0], value) \
            for i, value in enumerate(row)) for row in cursor.fetchall()]
    cursor.close()
    return jsonify(result), 200
