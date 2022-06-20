#helpers file for accessing connection_manager

import requests
from psycopg2 import pool
from flask import Response

URL = "http://connection-manager-service:5000"

db_url = "postgresql://root@cockroachdb-public:26257/defaultdb?sslmode=disable"

pool = pool.SimpleConnectionPool(1, 200, db_url)

DONE_FALSE = Response(
    response='{"done": false}',
    status=400,
    mimetype="application/json")
DONE_TRUE = Response(
    response='{"done": true}',
    status=200,
    mimetype="application/json")

class ReturnType(object):
    pass
def exec(sql, params, cm):
    if (cm):
        ip, conn_id = cm
        return requests.post(f"http://{ip}:5000/exec/{conn_id}", json= {"sql": sql, "params": params})
    return exec_psycopg(sql, params)

def get_one(sql, params, cm = None):
    response = exec(sql, params, cm)
    if response.status_code == 200:
        result = response.json()
        if len(result) == 1:
            return result[0], 200
    return DONE_FALSE

def get_all(sql, params, cm):
    response = exec(sql, params, cm)
    if response.status_code == 200:
        return {"items": response.json()}, 200
    return DONE_FALSE

def get_status(sql, params, cm):
    response = exec(f"{sql} RETURNING TRUE AS done;", params, cm)
    if response.status_code == 200:
        result = response.json()
        if len(result) == 1:
            return result[0], 200
    return '{"done": false}', 400

def start_tx():
    response = requests.get(f"{URL}/start_tx")
    while response.status_code != 200:
        response = requests.get(f"{URL}/start_tx")
    return response.content.decode("utf-8")

def commit_tx(cm):
    ip, conn_id = cm
    while requests.post(f"http://{ip}:5000/commit_tx/{conn_id}").status_code != 200:
        pass
    return

def cancel_tx(cm):
    ip, conn_id = cm
    while requests.post(f"http://{ip}:5000/cancel_tx/{conn_id}").status_code != 200:
        pass
    return

def exec_psycopg(sql, params):
    try:
        conn = pool.getconn()
    except Exception as err:
        print(f"Error getting connection\n{err}", flush=True)
        return False

    cursor = conn.cursor()

    try:
        cursor.execute(sql, params)
    except Exception as err:
        print(f"Error executing SQL: {sql}, {params}\n{err}", flush=True)

        cursor.close()
        conn.rollback()
        conn.close()
        pool.putconn(conn)

        res = ReturnType()
        res.status_code = 500
        error = err
        res.json = lambda: error
        return res

    if cursor.description is None:
        result = cursor.fetchall()
    else:
        result = [dict((cursor.description[i][0], value) \
            for i, value in enumerate(row)) for row in cursor.fetchall()]

    cursor.close()
    conn.commit()
    conn.close()
    pool.putconn(conn)

    res = ReturnType()
    res.status_code = 200
    res.json = lambda: result
    return res
