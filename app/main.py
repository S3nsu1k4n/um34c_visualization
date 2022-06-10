import os
from fastapi import FastAPI

from config import ServerConfig

app = FastAPI()


@app.get('/')
async def root():
    return {'message': 'Hello World'}


if __name__ == '__main__':
    os.system(f'uvicorn main:app '
              '--reload '
              f'--host {ServerConfig.HOST.value} '
              f'--port {ServerConfig.PORT.value} '
              )