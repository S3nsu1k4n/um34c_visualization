from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field, Required
from typing import Union, List
from enum import Enum
import time

from .bl_connection import BLDevice, BL_SOCK

router = APIRouter(
    prefix='/command',
    tags=['command'],
    dependencies=[],
    responses={}
)

RESPONSE_FORMAT = [{'length': 2, 'type': 'model', 'description': 'Model ID'},
                 {'length': 2, 'type': 'measurement', 'description': 'Voltage'},
                 {'length': 2, 'type': 'measurement', 'description': 'Amperage'},
                 {'length': 4, 'type': 'measurement', 'description': 'Wattage'},
                 {'length': 2, 'type': 'measurement', 'description': 'Temperature Celsius'},
                 {'length': 2, 'type': 'measurement', 'description': 'Temperature Fahrenheit'},
                 {'length': 2, 'type': 'configuration', 'description': 'Current selected data group, zero-zero-indexed'},
                 {'length': 80, 'type': 'measurement', 'description': 'Array of 10 main capacity data groups. For each data group: 4 bytes mAh, 4 bytes mWh'},
                 {'length': 2, 'type': 'measurement', 'description': 'USB data line voltage (positive) in centivolts'},
                 {'length': 2, 'type': 'measurement', 'description': 'USB data line voltage (negative) in centivolts'},
                 {'length': 2, 'type': 'measurement', 'description': 'Charging mode index'},
                 {'length': 4, 'type': 'measurement', 'description': 'mAh from threshold-based recording'},
                 {'length': 4, 'type': 'measurement', 'description': 'mWh from threshold-based recording'},
                 {'length': 2, 'type': 'configuration', 'description': 'Currently configured threshold for recording in centiamps'},
                 {'length': 4, 'type': 'measurement', 'description': 'Duration of threshold recording, in cumulative seconds'},
                 {'length': 2, 'type': 'configuration', 'description': 'Threshold recording active (1/0)'},
                 {'length': 2, 'type': 'configuration', 'description': 'Current screen timeout setting, in minutes (0-9)'},
                 {'length': 2, 'type': 'configuration', 'description': 'Current backlight setting (0-5)'},
                 {'length': 4, 'type': 'measurement', 'description': 'Resistance in deci-ohms'},
                 {'length': 2, 'type': 'configuration', 'description': 'Current screen'},
                 {'length': 1, 'type': 'unknown', 'description': 'Unknown'},
                 {'length': 1, 'type': 'checksum/unknown', 'description': 'Checksum or unknown'},
                 ]


class UM34CCommands(Enum):
    request_data = b'\xf0'
    next_screen = b'\xf1'
    rotate_screen = b'\xf2'
    previous_screen = b'\xf3'
    clear_data_group = b'\xf4'
    select_group = b'\xa0'
    recording_threshold = b'\xb0'
    backlight_level = b'\xd0'
    screen_timeout = b'\xe0'


class CommandResponse(BLDevice):
    command: Union[str, None] = Field(title='Used command')
    command_code: Union[str, None] = Field(title='Code of used command')


class UM34CResponseGroups(BaseModel):
    mAh: Union[str, None] = None
    mWh: Union[str, None] = None


class UM34CResponseBase(BaseModel):
    offset: Union[int, None] = None
    length: Union[int, None] = None
    type: Union[str, None] = None
    description: Union[str, None] = None


class UM34CResponseValues(UM34CResponseBase):
    value: Union[str, List[UM34CResponseGroups], None] = None


class UM34CResponse(CommandResponse):
    data: List[UM34CResponseValues]


def hex2int(val: str, divisor: int = 1) -> Union[int, float]:
    num = int(val, 16) / divisor
    if str(num).endswith('.0'):
        return int(num)
    return num


def decode_device_name(code: str):
    known_devices = {'0963': 'UM24C', '09c9': 'UM25C', '0d4c': 'UM34C'}
    return known_devices[code]


def decode_charging_mode(index: int):
    charging_modes = [{'value': 'UNKNOWN', 'description': 'Charging mode: Unknown, or normal (non-custom mode)'},
                      {'value': 'QC2', 'description': 'Charging mode: Qualcomm Quick Charge 2.0'},
                      {'value': 'QC3', 'description': 'Charging mode: Qualcomm Quick Charge 3.0'},
                      {'value': 'APP2.4A', 'description': 'Charging mode: Apple, max 2.4 Amp'},
                      {'value': 'APP2.1A', 'description': 'Charging mode: Apple, max 2.4 Amp'},
                      {'value': 'APP1.0A', 'description': 'Charging mode: Apple, max 2.4 Amp'},
                      {'value': 'APP0.5A', 'description': 'Charging mode: Apple, max 2.4 Amp'},
                      {'value': 'DCP1.5A', 'description': 'Charging mode: Dedicated Charging Port, max 1.5 Amp (D+ to D- short'},
                      {'value': 'SAMSUNG', 'description': 'Charging mode: Samsung (Adaptive Fast Charging'},]

    return charging_modes[index]


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
    data[0]['value'] = decode_device_name(data[0]['value'])
    data[16]['value'] = list(map(''.join, zip(*[iter(data[16]['value'])] * 8)))
    data[16]['value'] = [{'mAh': hex2int(x), 'mWh': hex2int(y)} for x, y in zip(data[16]['value'][0::2], data[16]['value'][1::2])]

    for k, divisor in zip([i for i in data.keys() if i not in [0, 16, 116, 128, 129]], [100, 1000, 1000, 1, 1, 1, 100, 100, 1, 1, 1, 100, 1, 1, 1, 10, 1]):
        data[k]['value'] = hex2int(data[k]['value'], divisor)
    data[100].update(decode_charging_mode(data[100]['value']))
    return data


def update_device_name(name: str):
    BL_SOCK.set_name(name=name)


def get_command_response(command: Enum, code: Union[bytes, None] = None) -> dict:
    code = command.value if code is None else code
    return {**BL_SOCK.get_info(), **{'command': command.name, 'command_code': '0' + str(code)[3:-1]}}


def add2hex(hex_val: bytes, add: int) -> bytes:
    val = int(hex_val.hex(), 16) + add
    return bytes.fromhex(hex(val)[2:])


@router.get('/request_data_raw', response_model=UM34CResponse)
async def request_data_raw():
    """
        Request a new 130 byte response of data from the device

        The response data will NOT be prepared and NOT decoded

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
        - mAh from threshold-based rcording
        - mWh from threshold-based rcording
        - Currently configured threshold for recording
        - Duration of threshold recording
        - Threshold recording active
        - Current screen timeout
        - Current backlight brightness
        - Resistance
        - Current screen
        """
    data = BL_SOCK.send_and_receive(command=UM34CCommands.request_data.value)

    response = data_preperation_raw(datastring=data)
    response[16]['value'] = list(map(''.join, zip(*[iter(response[16]['value'])] * 8)))
    response[16]['value'] = [{'mAh': x, 'mWh': y} for x, y in zip(response[16]['value'][0::2], response[16]['value'][1::2])]

    update_device_name(name=decode_device_name(response[0]['value']))

    response = {**get_command_response(UM34CCommands.request_data), 'data': [{'offset': k, **v} for k, v in response.items()]}
    return response


@router.get('/request_data', response_model=UM34CResponse)
async def request_data():
    """
    Request a new 130 byte response of data from the device

    The response data will be prepared and decoded

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
    - mAh from threshold-based rcording
    - mWh from threshold-based rcording
    - Currently configured threshold for recording
    - Duration of threshold recording
    - Threshold recording active
    - Current screen timeout
    - Current backlight brightness
    - Resistance
    - Current screen
    """
    data = BL_SOCK.send_and_receive(command=UM34CCommands.request_data.value)

    response = data_preperation_raw(datastring=data)
    response = data_preperation_decoded(data=response)

    response = {**get_command_response(UM34CCommands.request_data), 'data': [{'offset': k, **v} for k, v in response.items()]}
    return response


@router.get('/next_screen', response_model=CommandResponse)
async def next_screen():
    """
    Go to next screen
    """
    BL_SOCK.send(command=UM34CCommands.next_screen.value)
    return get_command_response(command=UM34CCommands.next_screen)


@router.get('/rotate_screen', response_model=CommandResponse)
async def rotate_screen(no_of_time: int = Query(default=1, description='How often it should rotate', ge=1, le=3)):
    """
    Rotate screen
    """
    for i in range(no_of_time):
        BL_SOCK.send(command=UM34CCommands.rotate_screen.value)
        if no_of_time > 1:
            time.sleep(0.9)
    return get_command_response(command=UM34CCommands.rotate_screen)


@router.get('/previous_screen', response_model=CommandResponse)
async def previous_screen():
    """
    Go to previous screen
    """
    BL_SOCK.send(command=UM34CCommands.previous_screen.value)
    return get_command_response(command=UM34CCommands.previous_screen)


@router.get('/clear_data_group', response_model=CommandResponse)
async def clear_data_group(group_no: Union[int, None] = Query(default=None, description='Number of group to delete data (optional)', ge=0, le=9)):
    """
    Delete data of current selected group

    If group number is given, the device will first switch to the group and then delete its data
    - without group number 🠖 current selected group data will be deleted
    - group_no = 1 🠖 select group number 1 then delete its data
    - group_no = 9 🠖 select group number 9 then delete its data
    """
    if group_no is not None:
        code = add2hex(UM34CCommands.select_group.value, group_no)
        BL_SOCK.send(command=code)
        time.sleep(0.03)
    BL_SOCK.send(command=UM34CCommands.clear_data_group.value)
    return get_command_response(command=UM34CCommands.clear_data_group)


@router.get('/select_data_group', response_model=CommandResponse)
async def select_data_group(group_no: int = Query(default=Required, description='Group number to switch to', ge=0, le=9)):
    """
    Set the selected data group between 0 and 9
    - 0 = set selected group to 0
    - 7 = set selected group to 7
    """
    code = add2hex(UM34CCommands.select_group.value, group_no)
    BL_SOCK.send(command=code)
    return get_command_response(command=UM34CCommands.select_group, code=code)


@router.get('/set_recording_threshold', response_model=CommandResponse)
async def set_recording_threshold(thresh: int = Query(default=Required, description='Threshold in centiamps', ge=0, le=30)):
    """
    Set recording threshold to a value between 0.00 and 0.30 A
    - 0 = 0.00 A
    - 5 = 0.05 A
    - 15 = 0.15 A
    - 30 = 0.30 A
    """
    code = add2hex(UM34CCommands.recording_threshold.value, thresh)
    BL_SOCK.send(command=code)
    return get_command_response(command=UM34CCommands.recording_threshold, code=code)


@router.get('/set_backlight_level', response_model=CommandResponse)
async def set_backlight_level(level: int = Query(default=Required, description='Device backlight level', ge=0, le=5)):
    """
    Set device backlight level between 0 and 5 (inclusive)
    - 0 = dim
    - 5 = full brightness
    """
    code = add2hex(UM34CCommands.backlight_level.value, level)
    BL_SOCK.send(command=code)
    return get_command_response(command=UM34CCommands.backlight_level, code=code)


@router.get('/set_screen_timeout', response_model=CommandResponse)
async def set_screen_timeout(minutes: int = Query(default=Required, description='Screen timeout in minutes', ge=0, le=9)):
    """
    Set screen timeout between 0 and 9 minutes (inclusive)
    - 0 = no screensaver
    - 1 = screensaver after 1 minute
    - 9 = screensaver after 9 minutes
    """
    code = add2hex(UM34CCommands.screen_timeout.value, minutes)
    BL_SOCK.send(command=code)
    return get_command_response(command=UM34CCommands.screen_timeout, code=code)
