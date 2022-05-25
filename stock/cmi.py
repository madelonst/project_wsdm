#helpers file for accessing connection_manager

import requests
import json

URL = "http://connection-manager:5000"

def exec(sql, params):
    return requests.post(URL + "/exec", json= {"sql": sql, "params": params})

def get_one(sql, params):
    response = exec(sql, params)
    if response.status_code == 200:
        return response.json()[0], 200
    return '{"done": false}', 200

def get_all(sql, params):
    response = exec(sql, params)
    if response.status_code == 200:
        return {"items": response.json()}, 200
    return '{"done": false}', 200

def get_status(sql, params):
    response = exec(sql + " RETURNING TRUE AS done", params)
    if response.status_code == 200:
        result = response.json()
        if len(result) == 1:
            return result[0], 200
    return '{"done": false}', 200