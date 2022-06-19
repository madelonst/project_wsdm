#helpers file for accessing connection_manager

import requests
from psycopg2 import pool
from flask import jsonify

URL = "http://connection-manager-service:5000"

db_url = "postgresql://root@cockroachdb-public:26257/defaultdb?sslmode=disable"

pool = pool.SimpleConnectionPool(1, 20, db_url)


class ReturnType(object):
    pass
def exec(sql, params, cm):
    if (cm):
        ip, conn_id = cm
        return requests.post(f"http://{ip}/exec/{conn_id}", json= {"sql": sql, "params": params})
    return exec_psycopg(sql, params)

def get_one(sql, params, cm = None):
    response = exec(sql, params, cm)
    if response.status_code == 200:
        return response.json()[0], 200
    return '{"done": false}', 400

def get_all(sql, params, cm):
    response = exec(sql, params, cm)
    if response.status_code == 200:
        return {"items": response.json()}, 200
    return '{"done": false}', 400

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
    while requests.post(f"http://{ip}/commit_tx/{conn_id}").status_code != 200:
        pass
    return

def cancel_tx(cm):
    ip, conn_id = cm
    while requests.post(f"http://{ip}/cancel_tx/{conn_id}").status_code != 200:
        pass
    return

def exec_psycopg(sql, params):
    conn = pool.getconn()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params)
    except Exception as err:
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
