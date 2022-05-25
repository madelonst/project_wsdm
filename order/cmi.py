#helpers file for accessing connection_manager

import requests
import json

URL = "http://connection-manager:5000"

def exec(sql, params, conn_id = None):
    if (conn_id):
        return requests.post("{}/exec/{}".format(URL, conn_id), json= {"sql": sql, "params": params})
    return requests.post(URL + "/exec", json= {"sql": sql, "params": params})

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
    response = exec(sql + " RETURNING TRUE AS done", params, conn_id)
    if response.status_code == 200:
        result = response.json()
        if len(result) == 1:
            return result[0], 200
    return '{"done": false}', 400

def start_tx():
    return requests.get("{}/start_tx".format(URL)).content

def commit_tx(conn_id):
    return requests.get("{}/commit_tx/{}".format(URL, conn_id))

def cancel_tx(conn_id):
    return requests.get("{}/cancel_tx/{}".format(URL, conn_id))