import sys
import base64
import json
import time
from datetime import datetime
from pathlib import Path
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
import psycopg as pg
from prompts import *


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


IMG_PATH = Path('images')
MODEL = 'gemma3:27b'
LLM_HOST = 'http://137.184.163.121:11444'


j2d = lambda x: json.loads(x.split('```')[1][4:])


def interpret_img(llm, fn_b64, sys_prompt):
    content = []
    for img_b64 in fn_b64:
        content.append({
            'type': 'image_url',
            'image_url': {
                'url': f'data:image/jpeg;base64,{img_b64}'
            }
        })

    msg = [
        sys_prompt,
        HumanMessage(content=content)
    ]

    response = llm.invoke(msg)
    return response.content


def get_sid_datetime(name: str) -> tuple[int, datetime]:
    sid = int(name.split('_')[1])
    dt = datetime.strptime(' '.join(name.split('_')[2:]), '%Y%m%d %H%M%S')
    return sid, dt


def interpret_process(llm, fn):
    try:
        sid, dt = get_sid_datetime(fn[0].name[:-4])
        
        fn_b64 = []
        for img in fn:
            with open(img,"rb") as f:
                fn_b64.append(base64.b64encode(f.read()).decode('utf-8'))
        
        tic = time.time()
        
        resp = interpret_img(llm, fn_b64, PROMPT_04)
        resp = j2d(resp)
        print(resp['cooking'])

        if resp['cooking']:
            resp = interpret_img(llm, fn_b64, PROMPT_05)
            resp = j2d(resp)
            print(resp['style'])
            style = resp['style']

            resp = interpret_img(llm, fn_b64, PROMPT_06)
            resp = j2d(resp)
            print(resp['ingredient'])
            ingredient = resp['ingredient']

            resp = interpret_img(llm, fn_b64, PROMPT_07)
            resp = j2d(resp)
            print(resp['desc'])
            desc = resp['desc']
 
            # write DB, IoT!proj2025s2
            with pg.connect(conn_str) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                    f'INSERT INTO image2 (session,datetime,ingredient,style,description)'
                    f' VALUES (%s, %s, %s, %s, %s)',
                        (sid, dt, ingredient, style, desc)
                    )
                conn.commit()
    
    except Exception as e:
        print(f'error: {str(e)}')
        return False
    
    finally:
        print('Time:', time.time()-tic)
    
    return True


if __name__ == "__main__":
    print(MODEL)
    llm = ChatOllama(model=MODEL,
                     base_url=LLM_HOST,
                     temperature=0.1)
    
    for folder in IMG_PATH.iterdir():
        if folder.is_dir():
            print('* in folder:', folder.name, end=', ') 
            fn = sorted([f for f in folder.rglob('*')])
            print(len(fn))
            if len(fn) != 0:
                for _ in range(2):
                    if interpret_process(llm, fn) is True:
                        break

