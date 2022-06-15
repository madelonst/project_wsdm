import atexit
from flask import Flask, request, jsonify
from psycopg2 import pool
import string
import random
from time import time
# from time import strftime

db_url = "postgresql://root@cockroachdb-public:26257/defaultdb?sslmode=disable"

print("STARTING POOL", flush=True)
pool = pool.SimpleConnectionPool(1, 200, db_url)

print("STARTING FLASK", flush=True)
app = Flask("connection-manager-service")

def close_db_connection():
    pool.closeall()
print("STARTING register", flush=True)
atexit.register(close_db_connection)

# @app.after_request
# def after_request(response):
#     timestamp = strftime('[%Y-%m-%d %H:%M:%S]')
#     print(f'{timestamp} [Flask request] {request.remote_addr} {request.method} {request.scheme} {request.full_path} {response.status}', flush=True)
#     return response

@app.post('/exec')
def execute_simple():
    print(time(), "ENTERING EXEC", flush=True)
    conn = pool.getconn()
    sql = request.json
    result = execute(conn, sql)
    commit(conn)
    print(time(), "RETURNING EXEC", flush=True)
    return result


@app.get('/start_tx')
def start_transaction():
    print(time(), "ENTERING START_TX", flush=True)
    conn_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 10))
    conn = pool.getconn(conn_id)
    print(time(), "RETURNING START_TX", flush=True)
    return conn_id, 200

@app.post('/exec/<conn_id>')
def execute_conn(conn_id: str):
    print(time(), "ENTERING EXEC WITH ID", conn_id, flush=True)
    conn = pool.getconn(conn_id)
    print(time(), "got connection", flush=True)
    sql = request.json
    print(time(), "starting execute", flush=True)
    res = execute(conn, sql)
    print(time(), "RETURNING EXEC", flush=True)
    return res

@app.post('/commit_tx/<conn_id>')
def commit_transaction(conn_id: str):
    print(time(), "ENTERING COMMIT_TX WITH ID", conn_id, flush=True)
    conn = pool.getconn(conn_id)
    commit(conn)
    print(time(), "RETURNING COMMIT_TX", flush=True)
    return "Success", 200

@app.post('/cancel_tx/<conn_id>')
def cancel_transaction(conn_id: str):
    print(time(), "ENTERING CANCEL_TX WITH ID", conn_id, flush=True)
    conn = pool.getconn(conn_id)
    conn.rollback()
    conn.close()
    pool.putconn(conn)
    print(time(), "RETURNING CANCEL_TX", flush=True)
    return "Success", 200


#Helper functions:
def execute(conn, sql):
    cursor = conn.cursor()
    print(time(), "got cursor", flush=True)
    try:
        cursor.execute("SELECT 1;")
        print(time(), "executed test", flush=True)
        cursor.execute(sql["sql"], sql["params"])
        print(time(), "executed sql", flush=True)
    except Exception as err:
        print(time(), "got an error when executing sql", flush=True)
        return "Error: " + str(err), 500
    if cursor.description is None:
        print(time(), "cursor has no description", flush=True)
        result = cursor.fetchall()
        print(time(), "fetched all from cursor", flush=True)
    else:
        print(time(), "cursor has a description", flush=True)
        result = [dict((cursor.description[i][0], value) \
            for i, value in enumerate(row)) for row in cursor.fetchall()]
        print(time(), "put results in a dict", flush=True)
    cursor.close()
    print(time(), "closed cursor", flush=True)
    return jsonify(result), 200

def commit(conn, conn_id = None):
    conn.commit()
    conn.close()
    pool.putconn(conn)

print("INIT DONE", flush=True)
