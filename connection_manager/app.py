import os
import atexit
from flask import Flask, request, jsonify
from psycopg2 import pool

db_url = "postgresql://root@cockroach-db:26257/defaultdb?sslmode=disable"

pool = pool.SimpleConnectionPool(1, 20, db_url)

app = Flask("connection-manager-service")

def close_db_connection():
    pool.close()
atexit.register(close_db_connection)

@app.post('/', defaults={'conn_id': None})
@app.post('/<conn_id>')
def create_item(conn_id: str):
    conn = pool.getconn(conn_id)
    cursor = conn.cursor()
    sql = request.get_data()
    try:
        cursor.execute(sql)
    except Exception as err:
        return "Error: " + str(err)
    if cursor.description is None:
        result = "Success"
    else:
        result = [dict((cursor.description[i][0], value) \
               for i, value in enumerate(row)) for row in cursor.fetchall()]
    cursor.close()
    conn.commit()
    pool.putconn(conn)
    return jsonify(result)