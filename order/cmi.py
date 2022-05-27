#helpers file for accessing connection_manager

import requests

URL = "http://connection-manager:5000"

def exec(sql, params, conn_id = None):
    if (conn_id):
        return requests.post(f"{URL}/exec/{conn_id}", json= {"sql": sql, "params": params})
    return requests.post(f"{URL}/exec", json= {"sql": sql, "params": params})

def get_one(sql, params, conn_id = None):
    response = exec(sql, params, conn_id)
    if response.status_code == 200:
        return response.json()[0], 200
    return '{"done": false}', 400

def get_all(sql, params, conn_id = None):
    response = exec(sql, params, conn_id)
    if response.status_code == 200:
        return {"items": response.json()}, 200
    return '{"done": false}', 400

def get_status(sql, params, conn_id = None):
    response = exec(f"{sql} RETURNING TRUE AS done", params, conn_id)
    if response.status_code == 200:
        result = response.json()
        if len(result) == 1:
            return result[0], 200
    return '{"done": false}', 400

def start_tx():
    return requests.get(f"{URL}/start_tx").content.decode('utf-8')

def commit_tx(conn_id):
    return requests.post(f"{URL}/commit_tx/{conn_id}")

def cancel_tx(conn_id):
    return requests.post(f"{URL}/cancel_tx/{conn_id}")