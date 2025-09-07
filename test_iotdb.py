import sys
import psycopg as pg


HOST = sys.argv[1].strip()
PORT = '5432'
DBNAME = 'iotdb'
OWNER = 'iotproj'
PASSWD = sys.argv[2].strip()
conn_owner = {'dbname': DBNAME,
              'host': HOST,
              'port': PORT,
              'user': OWNER,
              'password': PASSWD}
conn_str = f'postgresql://{OWNER}:{PASSWD}@{HOST}:{PORT}/{DBNAME}'


with pg.connect(conn_str) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT version()")
        result = cur.fetchone()
        print(result[0])


try:
    sql = sys.argv[3].strip()
    with pg.connect(conn_str) as conn:
        with conn.cursor() as cur:
            with open(sql) as f:
                cur.execute(f.read().strip())
            print('Done!')
except Exception as e:
    print(str(e))


