#helpers file for accessing the cockroach database

from psycopg2 import pool

db_url = "postgresql://root@cockroachdb-public:26257/defaultdb?sslmode=disable"

pool = pool.SimpleConnectionPool(1, 20, db_url)

def get_success(sql, params):
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
        return False
    cursor.close()
    conn.commit()
    conn.close()
    return True

def get_one(sql, params):
    try:
        conn = pool.getconn()
    except Exception as err:
        print(f"Error getting connection\n{err}", flush=True)
        return "", 500
    
    cursor = conn.cursor()

    try:
        cursor.execute(sql, params)
    except Exception as err:
        print(f"Error executing SQL: {sql}, {params}\n{err}", flush=True)
        cursor.close()
        conn.rollback()
        conn.close()
        return "", 500
    result = dict((cursor.description[i][0], value) for i, value in enumerate(cursor.fetchone()))
    cursor.close()
    conn.commit()
    conn.close()
    return result, 200
        