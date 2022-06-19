#helpers file for accessing connection_manager

import requests
from psycopg2 import pool
from flask import jsonify

URL = "http://connection-manager-service:5000"

#Starting and ending transaction:

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

#Executing sql through the connection manager:

def get_success(sql, params, cm):
    ip, conn_id = cm
    response = requests.post(f"http://{ip}/get_success/{conn_id}", json={"sql": sql, "params": params})
    return response.content, response.status_code

def get_one(sql, params, cm):
    ip, conn_id = cm
    response = requests.post(f"http://{ip}/get_one/{conn_id}", json={"sql": sql, "params": params})
    return response.json, response.status_code

def get_single(sql, params, cm):
    ip, conn_id = cm
    response = requests.post(f"http://{ip}/get_single/{conn_id}", json={"sql": sql, "params": params})
    return response.content, response.status_code

# BELOW THIS IS OLD CODE

# def exec(sql, params, cm = None):
#     if (cm):
#         ip, conn_id = tuple(cm.split(':'))
#         return requests.post(f"http://{ip}/exec/{conn_id}", json= {"sql": sql, "params": params})
#     return exec_psycopg(sql, params)



# def get_all(sql, params, cm = None):
#     response = exec(sql, params, cm)
#     if response.status_code == 200:
#         return {"items": response.json()}, 200
#     return '{"done": false}', 400

# def get_status(sql, params, cm):
#     response = exec(f"{sql} RETURNING TRUE AS done;", params, cm)
#     if response.status_code == 200:
#         result = response.json()
#         if len(result) == 1:
#             return result[0], 200
#     return '{"done": false}', 400