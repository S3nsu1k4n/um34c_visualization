import os
import time
from fastapi import FastAPI, Request

from config import ServerConfig

from .routers import bl_connection

app = FastAPI()
app.include_router(bl_connection.router)


@app.get('/')
async def root():
    return {'message': 'Hello World'}

@app.middleware('http')
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    print(process_time)
    response.headers['X-Process-Time'] = str(process_time)
    return response

if __name__ == '__main__':
    os.system(f'uvicorn main:app '
              '--reload '
              f'--host {ServerConfig.HOST.value} '
              f'--port {ServerConfig.PORT.value} '
              )