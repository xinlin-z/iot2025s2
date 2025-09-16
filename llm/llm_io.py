import sys
import base64
import json
import time
from pathlib import Path
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from prompts import *


IMG_PATH = Path('images')
MODEL = 'gemma3:27b'
LLM_HOST = 'http://159.203.58.5:11444'


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
            resp = interpret_img(llm, img_b64, PROMPT_02)
            resp = j2d(resp)
            print('step 2:', resp)
            if len(resp['ingredient']) != 0:
                resp = interpret_img(llm, img_b64, PROMPT_03)
                resp = j2d(resp)
                print('step 3:', resp)
    
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
    
    for img in IMG_PATH.iterdir():
        print('*', img)
        
        # give each image two chances
        for _ in range(2):
            if interpret_process(llm, img) is True:
                break

