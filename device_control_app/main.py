import os
import time
from fastapi import FastAPI, Request, Depends
from fastapi.responses import FileResponse
from functools import lru_cache
from config import ServerSettings, Settings

from routers import bl_connection, commands

description = """
    UM34C API to easily control and receive data from an UM34C device via an API.
    
    ## bluetooth
    
    Provides bluetooth related functions to easily find nearby devices and connect, disconnect to the device.
    
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
    version='2022.07.05',
    openapi_tags=[{'name': 'bluetooth', 'description': 'Commands connecting to UM34C'},
                  {'name': 'command', 'description': 'Commands controlling UM34C'}]
)
app.include_router(bl_connection.router)
app.include_router(commands.router)


@app.get('/', include_in_schema=False)
async def root():
    return FileResponse('./static/templates/index.html')


@lru_cache()
def get_settings():
    return Settings()


@app.get('/info', response_model=Settings, summary='Get settings values', response_description='Settings values', tags=['main'])
async def info(settings: Settings = Depends(get_settings)):
    return settings


@app.middleware('http')
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers['X-Process-Time'] = str(process_time)
    response.headers.update({'X-Command-URL': request.url.path})
    return response


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse('./static/images/um34c32x32.ico')


@app.get("/apple-touch-icon.png", include_in_schema=False)
async def apple_touch_icon():
    return FileResponse('./static/images/um34c180x180.png')


@app.get("/apple-touch-icon-precomposed.png", include_in_schema=False)
async def apple_touch_icon_composed():
    return FileResponse('./static/images/um34c180x180.png')


if __name__ == '__main__':
    os.system(f'uvicorn main:app '
              '--reload '
              f'--host {ServerSettings().host} '
              f'--port {ServerSettings().port} '
              )