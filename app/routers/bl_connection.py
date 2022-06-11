from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field, Required
from typing import Union, List, Dict
import bluetooth
from functools import reduce
from config import UM34CConfig

router = APIRouter(
    prefix='/bl',
    tags=['bluetooth'],
    dependencies=[],
    responses={}
)


class BLDevice(BaseModel):
    name: Union[str, None] = None
    bd_addr: Union[str, None] = Field(default=None, title='bd_address', min_length=17, max_length=17)


def search_nearby_devices():
    data = []
    for device in bluetooth.discover_devices(lookup_names=True):
        data.append({'name': device[1], 'bd_addr': device[0]})
    if len(data) == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='No bluetooth device found',
                            headers={'X-Error': 'No bluetooth device found'}
                            )
    return data


@router.get('/nearby', response_model=List[BLDevice])
async def get_nearby_devices():
    """
    Search nearby bluetooth devices and return a list of names and their adresses
    """
    return search_nearby_devices()


@router.get('/connect_by_devicename')
async def connect_by_devicename(device_name: str):
    """
    1. Step: Search nearby bluetooth devices
    2. Step: Check if device_name is found
    3. Step: Connect to the device with the found bd_address:

    - **device_name**: The name of the device to connect to via bluetooth
    """
    found_devices = search_nearby_devices()
    bd_address = None
    for device in found_devices:
        if device_name == device['name']:
            bd_address = device['bd_addr']
            print(bd_address)

    if bd_address is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Bluetooth address of '{device_name}' not found",
                            headers={'X-Error': f'Bluetooth address of "{device_name}" not found'}
                            )

    # TODO connect with found address
    print('FOUND', bd_address)


@router.get('/connect_by_bd_address')
async def connect_by_address(bd_addr: str = Query(default=Required, description='Bluetooth Device Address to connect to', max_length=17, min_length=17)):
    """
    Connect to the device with the specified bd_address:

    - **bd_addr**: The Bluetooth Device Address to connect to
    """
    print('Connecting with', bd_addr)
    # TODO connect with address
