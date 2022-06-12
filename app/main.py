import os
import time
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from config import ServerConfig

from .routers import bl_connection, commands

app = FastAPI()
app.include_router(bl_connection.router)
app.include_router(commands.router)


@app.get('/')
async def root():
    content = """
    <!DOCTYPE html>
    <html>
    <body>
    <h1>UM34C with FastAPI</h1>
     <a href="/docs">docs</a> 
    </body>
    </html>
    """
    return HTMLResponse(content=content)


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