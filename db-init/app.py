import psycopg2

db_url = "postgresql://root@cockroachdb-public:26257/defaultdb?sslmode=disable"
conn = psycopg2.connect(db_url)

with conn.cursor() as cur:
    cur.execute(
        "DROP TABLE IF EXISTS stock;"
    )
    conn.commit()
    cur.execute(
        "CREATE TABLE stock (item_id INT PRIMARY KEY, unit_price NUMERIC, stock_qty INT);"
    )
    conn.commit()
    cur.execute(
        "DROP TABLE IF EXISTS order_headers;"
    )
    conn.commit()
    cur.execute(
        "CREATE TABLE order_headers (order_id INT PRIMARY KEY, user_id INT, paid BOOLEAN);"
    )
    conn.commit()
    cur.execute(
        "DROP TABLE IF EXISTS order_items;"
    )
    conn.commit()
    cur.execute(
        "CREATE TABLE order_items (order_id INT, item_id INT, count INT, CONSTRAINT \"primary\" PRIMARY KEY (order_id, item_id));"
    )
    conn.commit()
    cur.execute(
        "DROP TABLE IF EXISTS accounts;"
    )
    conn.commit()
    cur.execute(
        "CREATE TABLE accounts (user_id INT PRIMARY KEY, credit NUMERIC);"
    )
    conn.commit()

conn.close()
