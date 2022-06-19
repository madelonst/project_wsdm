#helpers file for performing queries

import cmi
import cri

def get_success(sql, params, cm = None):
    if cm != None:
        return cmi.get_success(sql, params, cm)
    return cri.get_success(sql, params)

def get_one(sql, params, cm = None):
    if cm != None:
        return cmi.get_one(sql, params, cm)
    return cri.get_one(sql, params)


def get_done(sql, params, cm = None):
    if not get_success(sql, params, cm):
        return {"done": False}, 400
    return {"done": True}, 200
        