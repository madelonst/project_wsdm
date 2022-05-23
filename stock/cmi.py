#helpers file for accessing connection_manager

import requests

URL = "http://connection-manager:5000"

def exec(sql):
    return requests.post(URL + "/exec", data = sql)