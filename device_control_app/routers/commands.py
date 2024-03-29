from multiprocessing.dummy import Process
from fastapi import APIRouter, Query, Path, Depends
from fastapi.responses import FileResponse
from pydantic import Field, Required
from typing import Union, List
from enum import Enum
import time
from datetime import datetime
import json
import requests


from .commands_dependencies import verify_key_allowed, verify_keys_allowed
from .commands_models import (UM34CResponseRaw,
                              UM34CResponse,
                              CommandResponse,
                              RESPONSE_FORMAT,
                              KNOWN_DEVICES,
                              CHARGING_MODES,
                              UM34CCommands,
                              UM34CResponseDataRaw,
                              UM34Examples,
                              BLErrorMessage400, BLErrorMessage404, BLErrorMessage409,
                              DBResponse
                              )
from .bl_connection import get_bluetooth_device

router = APIRouter(
    prefix='/command',
    tags=['command'],
    dependencies=[],
    responses={400: {'model': BLErrorMessage400},
               404: {'model': BLErrorMessage404},
               409: {'model': BLErrorMessage409}}
)


def hex2int(val: str, divisor: int = 1) -> Union[int, float]:
    num = int(val, 16) / divisor
    if str(num).endswith('.0'):
        return int(num)
    return num


def data_preperation_raw(datastring: str = Field(default=Required, min_length=130, max_length=130)) -> dict:
    response_data = dict()
    offset = 0
    for meta in RESPONSE_FORMAT:
        response_data[offset // 2] = meta
        data = datastring[offset:offset + meta['length'] * 2]
        response_data[offset // 2].update({'value': data})
        offset += meta['length'] * 2
    return response_data


def data_preperation_decoded(data: dict) -> dict:
    data[0]['value'] = KNOWN_DEVICES[data[0]['value']]
    data[16]['value'] = list(map(''.join, zip(*[iter(data[16]['value'])] * 8)))
    data[16]['value'] = [{'mah': hex2int(x), 'mwh': hex2int(y)} for x, y in zip(data[16]['value'][0::2], data[16]['value'][1::2])]

    for k, divisor in zip([i for i in data.keys() if i not in [0, 16, 128, 129]], [100, 1000, 1000, 1, 1, 1, 100, 100, 1, 1, 1, 100, 1, 1, 1, 1, 10, 1]):
        data[k]['value'] = hex2int(data[k]['value'], divisor)
    data[100].update(CHARGING_MODES[data[100]['value']])

    units = {0: 'None', 2: 'V', 4: 'A', 6: 'W', 10: 'C', 12: 'F', 14: '1', 16: 'mAh/mWh', 96: 'V', 98: 'V', 100: 'None', 102: 'mAh', 106: 'mWh', 110: 'A', 112: 's', 116: 'None', 118: 'min', 120: '1', 122: 'Ω', 126: '1'}
    for offset, unit in units.items():
        data[offset].update({'value_unit': unit})
    return data


def get_command_response(bl_device, command: Enum, code: Union[bytes, None] = None) -> dict:
    code = command.value if code is None else code
    return {**{'timestamp': datetime.now()}, **bl_device.get_info(), **{'command': command.name, 'command_code': '0' + str(code)[3:-1]}}


def add2hex(hex_val: bytes, add: int) -> bytes:
    val = int(hex_val.hex(), 16) + add
    return bytes.fromhex(hex(val)[2:])


def get_model_keys(model) -> list:
    return list(model.schema()['properties'])


def filter_response_data(*, data: dict, q=List[str]) -> dict:
    response_q = {}
    for query in q:
        if query in data.keys():
            response_q[query] = data[query]

    return response_q


def get_response_data(bl_device,
                      q: Union[List[str], None] = None, raw: bool = False, values_only: bool = False,) -> dict:
    data = bl_device.send_and_receive(command=UM34CCommands.request_data.value)
    response = data_preperation_raw(datastring=data)

    if raw:
        response[16]['value'] = list(map(''.join, zip(*[iter(response[16]['value'])] * 8)))
        response[16]['value'] = [{'mah': x, 'mwh': y} for x, y in zip(response[16]['value'][0::2], response[16]['value'][1::2])]
    else:
        response = data_preperation_decoded(data=response)

    response_new = {}
    for key, (k, v) in zip(get_model_keys(UM34CResponseDataRaw), response.items()):
        if not values_only:
            response_new[key] = {'byte_offset': k, **v, 'byte_length': v['length'], 'value_type': type(v['value']).__name__}
        else:
            response_new[key] = {'value': v['value']}
    if q is not None:
        response_new = filter_response_data(data=response_new, q=q)

    return {**get_command_response(bl_device, UM34CCommands.request_data), 'data': [response_new]}


@router.get('/', include_in_schema=False)
async def command_index():
    return FileResponse('./app/static/templates/commands_index.html')


@router.get('/request_data_raw', response_model=UM34CResponseRaw, response_model_exclude_unset=True,
            summary='Receive raw data from device',
            response_description='Successfully sent command to device')
async def request_data_raw(bl_device = Depends(get_bluetooth_device),
                           keys: Union[List[str], None] = Depends(verify_keys_allowed),
                           values_only: bool = Query(default=False, description='If data should only contain values')):
    """
    Request a new 130 byte response of data from the device (NOT decoded)
    - **key** : filter data by given keys
    - **values_only** : If data should only contain values

    Data contains:
    - Model ID
    - Voltage
    - Amperage
    - Wattage
    - Temperature Celsius
    - Temperature Fahrenheit
    - Current selected data group
    - Data of the data groups
    - USB data line voltage (positive)
    - USB data line voltage (negative)
    - Charging mode
    - mAh from threshold-based recording
    - mWh from threshold-based recording
    - Currently configured threshold for recording
    - Duration of threshold recording
    - Threshold recording active
    - Current screen timeout
    - Current backlight brightness
    - Resistance
    - Current screen
    """
    return get_response_data(bl_device=bl_device, q=keys, raw=True, values_only=values_only)


@router.get('/request_data_raw/{key}', response_model=UM34CResponseRaw, response_model_exclude_unset=True,
            summary='Receive specific raw data from device',
            response_description='Successfully sent command to device'
            )
async def request_data_raw(bl_device = Depends(get_bluetooth_device),
                           key: str = Depends(verify_key_allowed),
                           values_only: bool = Query(default=False, description='If data should only contain values')):
    """
    Request a new 130 byte response of data from the device filtered by given key (NOT decoded)
    - **key** : filter data by given keys
    - **values_only** : If data should only contain values

    Data contains:
    - Model ID
    - Voltage
    - Amperage
    - Wattage
    - Temperature Celsius
    - Temperature Fahrenheit
    - Current selected data group
    - Data of the data groups
    - USB data line voltage (positive)
    - USB data line voltage (negative)
    - Charging mode
    - mAh from threshold-based recording
    - mWh from threshold-based recording
    - Currently configured threshold for recording
    - Duration of threshold recording
    - Threshold recording active
    - Current screen timeout
    - Current backlight brightness
    - Resistance
    - Current screen
    """
    return get_response_data(bl_device=bl_device, q=[key], raw=True, values_only=values_only)


@router.get('/request_data', response_model=UM34CResponse, response_model_exclude_unset=True,
            summary='Receive data from device',
            response_description='Successfully sent command to device'
            )
async def request_data(bl_device = Depends(get_bluetooth_device),
                       keys: Union[List[str], None] = Query(default=None, description='Filter data by key', examples=UM34Examples.request_data_q),
                       values_only: bool = Query(default=False, description='If data should only contain values'),):
    """
    Request a new 130 byte response of data from the device (decoded)
    - **key** : filter data by given keys
    - **values_only** : If data should only contain values

    Data contains:
    - Model ID
    - Voltage
    - Amperage
    - Wattage
    - Temperature Celsius
    - Temperature Fahrenheit
    - Current selected data group
    - Data of the data groups
    - USB data line voltage (positive)
    - USB data line voltage (negative)
    - Charging mode
    - mAh from threshold-based recording
    - mWh from threshold-based recording
    - Currently configured threshold for recording
    - Duration of threshold recording
    - Threshold recording active
    - Current screen timeout
    - Current backlight brightness
    - Resistance
    - Current screen
    """
    return get_response_data(bl_device=bl_device, q=keys, values_only=values_only)


@router.get('/request_data/{key}', response_model=UM34CResponse, response_model_exclude_unset=True,
            summary='Receive specific data from device',
            response_description='Successfully sent command to device'
            )
async def request_data_by_key(bl_device = Depends(get_bluetooth_device),
                              key: str = Depends(verify_key_allowed),
                              values_only: bool = Query(default=False, description='If data should only contain values')):
    """
    Request a new 130 byte response of data from the device filtered by given key (decoded)
    - **key** : filter data by given keys
    - **values_only** : If data should only contain values

    Data contains:
    - Model ID
    - Voltage
    - Amperage
    - Wattage
    - Temperature Celsius
    - Temperature Fahrenheit
    - Current selected data group
    - Data of the data groups
    - USB data line voltage (positive)
    - USB data line voltage (negative)
    - Charging mode
    - mAh from threshold-based recording
    - mWh from threshold-based recording
    - Currently configured threshold for recording
    - Duration of threshold recording
    - Threshold recording active
    - Current screen timeout
    - Current backlight brightness
    - Resistance
    - Current screen
    """
    return get_response_data(bl_device=bl_device, q=[key], values_only=values_only)


@router.get('/next_screen', response_model=CommandResponse,
                            summary='Go to next screen on device',
                            response_description='Successfully sent command to device',
                            )
async def next_screen(bl_device = Depends(get_bluetooth_device)):
    """
    Go to next screen
    """
    bl_device.send(command=UM34CCommands.next_screen.value)
    return get_command_response(bl_device=bl_device, command=UM34CCommands.next_screen)


@router.get('/rotate_screen', response_model=CommandResponse, summary='Rotate screen on device', response_description='Successfully sent command to device')
async def rotate_screen(bl_device = Depends(get_bluetooth_device), no_of_time: int = Query(default=1, description='How often it should rotate', ge=1, le=3)):
    """
    Rotates the screen
    - **no_if_time** : How often it should rotate
    """
    for i in range(no_of_time):
        bl_device.send(command=UM34CCommands.rotate_screen.value)
        if no_of_time > 1:
            time.sleep(0.9)
    return get_command_response(bl_device=bl_device, command=UM34CCommands.rotate_screen)


@router.get('/previous_screen', response_model=CommandResponse, summary='Go to previous screen on device', response_description='Successfully sent command to device')
async def previous_screen(bl_device = Depends(get_bluetooth_device)):
    """
    Go to previous screen
    """
    bl_device.send(command=UM34CCommands.previous_screen.value)
    return get_command_response(bl_device=bl_device, command=UM34CCommands.previous_screen)


@router.get('/clear_data_group', response_model=CommandResponse, summary='Clear data of a group', response_description='Successfully sent command to device')
async def clear_data_group(bl_device = Depends(get_bluetooth_device), group_no: Union[int, None] = Query(default=None, description='Number of group to delete data (optional)', ge=0, le=9, examples=UM34Examples.clear_data_group)):
    """
    Delete data of current selected group
    - **group_no** : Number of group to delete data (optional)

    If group number is given, the device will first switch to the group and then delete its data
    - without group number 🠖 current selected group data will be deleted
    - group_no = 1 🠖 select group number 1 then delete its data
    - group_no = 9 🠖 select group number 9 then delete its data
    """
    code = UM34CCommands.clear_data_group.value
    if group_no is not None:
        code = add2hex(UM34CCommands.select_group.value, group_no)
        bl_device.send(command=code)
        time.sleep(0.03)
    bl_device.send(command=UM34CCommands.clear_data_group.value)
    return get_command_response(bl_device=bl_device, command=UM34CCommands.clear_data_group, code=code)


@router.get('/select_data_group/{group_no}', response_model=CommandResponse, summary='Select a data group', response_description='Successfully sent command to device')
async def select_data_group(bl_device = Depends(get_bluetooth_device), group_no: int = Path(default=Required, description='Group number to switch to', ge=0, le=9, examples=UM34Examples.select_data_group)):
    """
    Set the selected data group between 0 and 9
    - **group_no** : Number of group to delete data (optional)


    - 0 = set selected group to 0
    - 7 = set selected group to 7
    """
    code = add2hex(UM34CCommands.select_group.value, group_no)
    bl_device.send(command=code)
    return get_command_response(bl_device=bl_device, command=UM34CCommands.select_group, code=code)


@router.get('/set_recording_threshold/{centi_amps}', response_model=CommandResponse, summary='Set the threshold amps', response_description='Successfully sent command to device')
async def set_recording_threshold(bl_device = Depends(get_bluetooth_device), centi_amps: int = Path(default=Required, description='Threshold in centiamps', ge=0, le=30, examples=UM34Examples.set_recording_threshold)):
    """
    Set recording threshold to a value between 0.00 and 0.30 A
    - **centi_amps** : Threshold in centiamps

    - 0 = 0.00 A
    - 5 = 0.05 A
    - 15 = 0.15 A
    - 30 = 0.30 A
    """
    code = add2hex(UM34CCommands.recording_threshold.value, centi_amps)
    bl_device.send(command=code)
    return get_command_response(bl_device=bl_device, command=UM34CCommands.recording_threshold, code=code)


@router.get('/set_backlight_level/{level}', response_model=CommandResponse, summary='Set backlight level of device', response_description='Successfully sent command to device')
async def set_backlight_level(bl_device = Depends(get_bluetooth_device), level: int = Path(default=Required, description='Device backlight level', ge=0, le=5, examples=UM34Examples.set_backlight)):
    """
    Set device backlight level between 0 and 5 (inclusive)
    - **level** : Device backlight level

    - 0 = dim
    - 5 = full brightness
    """
    code = add2hex(UM34CCommands.backlight_level.value, level)
    bl_device.send(command=code)
    return get_command_response(bl_device=bl_device, command=UM34CCommands.backlight_level, code=code)


@router.get('/set_screen_timeout/{minutes}', response_model=CommandResponse, summary='Set screen timeout of device', response_description='Successfully sent command to device')
async def set_screen_timeout(bl_device = Depends(get_bluetooth_device), minutes: int = Path(default=Required, description='Screen timeout in minutes', ge=0, le=9, examples=UM34Examples.set_screen_timeout)):
    """
    Set screen timeout between 0 and 9 minutes (inclusive)
    - **minutes** : Screen timeout in minutes

    - 0 = no screensaver
    - 1 = screensaver after 1 minute
    - 9 = screensaver after 9 minutes
    """
    code = add2hex(UM34CCommands.screen_timeout.value, minutes)
    bl_device.send(command=code)
    return get_command_response(bl_device=bl_device, command=UM34CCommands.screen_timeout, code=code)


@router.get('/set_screen/{no}', response_model=CommandResponse, summary='Go to a specific screen on device', response_description='Successfully sent command to device')
async def set_screen(bl_device = Depends(get_bluetooth_device), no: int = Path(default=Required, description='Number of screen to go to', ge=0, le=5, examples=UM34Examples.set_screen)):
    """
    Go to a specific screen (0 - 5)
    - **no** : Number of screen to go to

    - 0 = go to most left screen
    - 3 = go to screen number 3
    - 5 = go to most right screen

    Uses the next/previous screen command multiple times to go to the selected screen
    """
    data = bl_device.send_and_receive(command=UM34CCommands.request_data.value)
    response = data_preperation_raw(datastring=data)
    cur_screen = int(response[126]['value'])
    diff = no - cur_screen
    if diff != 0:
        command = UM34CCommands.next_screen if diff > 0 else UM34CCommands.previous_screen
        for i in range(abs(diff)-1):
            bl_device.send(command=command.value)
        bl_device.send(command=command.value)
        return get_command_response(bl_device=bl_device, command=command)
    else:
        return {**{'timestamp': datetime.now()}, **bl_device.get_info(), **{'command': None, 'command_code': None}}


@router.get('/reset_device', response_model=CommandResponse, summary='Reset the device', response_description='Successfully sent command to device')
async def reset_device(bl_device = Depends(get_bluetooth_device)):
    """
    Resetting the device
    - set screen to the most left one
    - delete data of all groups
    - set backlight to level 5
    - set screen timeout to 1 minute
    """
    data = bl_device.send_and_receive(command=UM34CCommands.request_data.value)
    response = data_preperation_raw(datastring=data)
    cur_screen = int(response[126]['value'])
    diff = 0 - cur_screen
    if diff != 0:
        command = UM34CCommands.next_screen if diff > 0 else UM34CCommands.previous_screen
        for i in range(abs(diff)-1):
            bl_device.send(command=command.value)
            time.sleep(0.3)
        bl_device.send(command=command.value)

    for group_no in range(10):
        code = add2hex(UM34CCommands.select_group.value, group_no)
        bl_device.send(command=code)
        time.sleep(0.05)
        bl_device.send(command=UM34CCommands.clear_data_group.value)
        time.sleep(0.3)
    bl_device.send(command=UM34CCommands.select_group.value)

    code = add2hex(UM34CCommands.backlight_level.value, 5)
    bl_device.send(command=code)

    code = add2hex(UM34CCommands.screen_timeout.value, 1)
    bl_device.send(command=code)

    return {**{'timestamp': datetime.now()}, **bl_device.get_info(), **{'command': None, 'command_code': None}}

request_session = requests.Session()
request_session.trust_env = False
url = 'http://127.0.0.1:8081/data'


class SendingProcess(Process):
    def __init__(self):
        Process.__init__(self)
        self.run_loop = True
        self.in_loop = False

    def run(self):
        self.in_loop = True
        while self.run_loop:
            gen = get_bluetooth_device()
            try:
                for bl_device in gen:
                    data = get_response_for_db(bl_device)
                    resp = request_session.post(url=url, json=data)
                time.sleep(0.01)
            except:
                pass
            finally:
                pass
        self.in_loop = False

    def terminate(self):
        self.run_loop = False
        while self.in_loop: pass


sending_process = SendingProcess()
sending_process.setDaemon(True)


def get_response_for_db(bl_device):
    response = get_response_data(bl_device=bl_device)
    return {'created_at': str(datetime.now()), 'bd_address': bl_device.get_info()['bd_address'], **{k: v['value'] for k, v in response['data'][0].items()}}


@router.get('/send_response_to_db', response_model=DBResponse, summary='Sends device response to db', response_description='Successfully sent data from device to db')
async def send_response_to_db(bl_device = Depends(get_bluetooth_device)):
    """
    Gets data from the bluetooth device and sends it to the database to store the data
    - Response: id number of created data line in database
    """
    data = get_response_for_db(bl_device)
    resp = request_session.post(url=url, json=data)
    
    try:
        content = json.loads(resp.content)
        content.update({'message': 'OK'})
    except json.decoder.JSONDecodeError:
        content = {'message': resp.content.decode('utf-8')}
    return content


@router.get('/send_response_to_db_loop', response_model=None, summary='Sends device response to db in loop', response_description='Successfully started process')
async def send_response_to_db_loop():
    """
    Starts process of a loop to get data from the bluetooth device and send it to the database to store the data
    """
    global sending_process
    sending_process.terminate()
    sending_process = SendingProcess()
    sending_process.setDaemon(True)
    sending_process.start()
    return {'message': 'Started sending to db process loop'}


@router.get('/stop_sending_loop', response_model=None, summary='Sends device response to db', response_description='Successfully stopped process')
async def stop_sending_loop():
    """
    Stops process with the loop which gets data from the bluetooth device and sends it to the database to store the data
    """
    sending_process.terminate()
    
    return {'message': 'Stopped sending to db process loop'}
