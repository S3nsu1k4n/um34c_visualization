import os
import time
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from config import ServerConfig

from .routers import bl_connection, commands

description = """
    UM34C API to easily control and receive data from an UM34C device via an API.
    
    ## bluetooth
    
    Provides bluetooth related functions to easily connect and disconnect to the device.
    
    ## command
    
    Provides all commands possible to control the device
    * **requesting data from device (decoded or raw)**
    * **go to next screen**
    * **to to previous screen**
    * **go to a specific screen**
    * **rotate screen**
    * **delete data of a group**
    * **select a group**
    * **setting threshold**
    * **setting backlight of the screen**
    * **setting timeout of the screen**
    * **resetting the device**
"""

app = FastAPI(
    title='UM34C with FastAPI',
    description=description,
    version='2022.06.14',
    openapi_tags=[{'name': 'bluetooth', 'description': 'Commands connecting to UM34C'},
                  {'name': 'command', 'description': 'Commands controlling UM34C'}]
)
app.include_router(bl_connection.router)
app.include_router(commands.router)


@app.get('/', include_in_schema=False)
async def root():
    return FileResponse('./app/static/templates/index.html')


@app.middleware('http')
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers['X-Process-Time'] = str(process_time)
    response.headers.update({'X-Command-URL': request.url.path})
    connected_since, disconnected_since = bl_connection.BL_SOCK.get_connected_timestamps()
    if connected_since is not None:
        response.headers.update({'x-bluetooth-connected-since': str(connected_since)})
    if disconnected_since is not None:
        response.headers.update({'x-bluetooth-not-connected-since': str(disconnected_since)})
    return response


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse('app/static/images/um34c32x32.ico')


@app.get("/apple-touch-icon.png", include_in_schema=False)
async def apple_touch_icon():
    return FileResponse('app/static/images/um34c180x180.png')


@app.get("/apple-touch-icon-precomposed.png", include_in_schema=False)
async def apple_touch_icon_composed():
    return FileResponse('app/static/images/um34c180x180.png')


if __name__ == '__main__':
    os.system(f'uvicorn main:app '
              '--reload '
              f'--host {ServerConfig.HOST.value} '
              f'--port {ServerConfig.PORT.value} '
              )