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
LLM_HOST = 'http://146.190.249.52:11444'


j2d = lambda x: json.loads(x.split('```')[1][4:])


def interpret_img(llm, img_b64, sys_prompt):
    msg = [
        sys_prompt,
        HumanMessage(
            content=[
                {
                    'type': 'text',
                    'text': 'This is the image.'
                },
                {
                    'type': 'image_url',  # For base64, use 'image_url' with a data URL
                    'image_url': {
                        'url': f'data:image/jpeg;base64,{img_b64}'
                    },
                },
            ]
        )
    ]

    response = llm.invoke(msg)
    return response.content


def get_sid_datetime(name: str) -> tuple[int, datetime]:
    sid = int(name.split('_')[1])
    dt = datetime.strptime(' '.join(name.split('_')[2:]), '%Y%m%d %H%M%S')
    return sid, dt


def interpret_process(llm, img):    
    try:
        tic = time.time()
        # base64
        with open(img,"rb") as f:
            img_b64 = base64.b64encode(f.read()).decode('utf-8')
        
        # step 1: if cooking
        resp = interpret_img(llm, img_b64, PROMPT_01)
        resp = j2d(resp)
        print('step 1:', resp)
        
        # step 2 & 3: ingredient & style
        if resp['cooking']:
            sid, dt = get_sid_datetime(img.name[:-4])
            resp = interpret_img(llm, img_b64, PROMPT_02)
            resp = j2d(resp)
            print('step 2:', resp)
            if len(resp['ingredient']) != 0:
                ingredient = ' '.join(resp['ingredient'])
                resp = interpret_img(llm, img_b64, PROMPT_03)
                resp = j2d(resp)
                print('step 3:', resp)
                style = resp['style']
            else:
                ingredient = None
                style = None
            
            # write DB
            with pg.connect(conn_str) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f'INSERT INTO image (session,datetime,ingredient,style)'
                        f' VALUES (%s, %s, %s, %s)',
                         (sid, dt, ingredient, style)
                    )
                conn.commit()
    
    except Exception as e:
        print(f'{img}, error: {str(e)}')
        return False
    
    finally:
        print('Time:', time.time()-tic)
    
    return True


if __name__ == "__main__":
    print(MODEL)
    llm = ChatOllama(model=MODEL,
                     base_url=LLM_HOST,
                     temperature=0.1)
    
    with open('fskip.txt') as f:
        fskip = f.readlines()
    fskip = list(map(lambda x:x.strip(), fskip))
    
    for img in IMG_PATH.rglob('*'):
        if img.is_file():
            if img.name in fskip:
                continue
            
            print('*', img)
            fskip.append(img.name)
            
            # give each image two chances
            for _ in range(2):
                if interpret_process(llm, img) is True:
                    break

            # save
            with open('fskip.txt', 'a+') as f:
                f.write(img.name+'\n')
