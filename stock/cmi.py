#helpers file for accessing connection_manager

import requests
import json

URL = "http://connection-manager:5000"

def exec(sql, params):
    return requests.post(URL + "/exec", json= {"sql": sql, "params": params})