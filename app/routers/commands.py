from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field, Required
from typing import Union, List
from enum import Enum
import time
from datetime import datetime


from .bl_connection import BLDevice, BL_SOCK

router = APIRouter(
    prefix='/command',
    tags=['command'],
    dependencies=[],
    responses={}
)

RESPONSE_FORMAT = [{'length': 2, 'type': 'model', 'description': 'Model ID'},
                 {'length': 2, 'type': 'measurement', 'description': 'Current measured voltage'},
                 {'length': 2, 'type': 'measurement', 'description': 'Current measured amperage'},
                 {'length': 4, 'type': 'measurement', 'description': 'Current measured wattage'},
                 {'length': 2, 'type': 'measurement', 'description': 'Current measured temperature Celsius'},
                 {'length': 2, 'type': 'measurement', 'description': 'Current measured temperature Fahrenheit'},
                 {'length': 2, 'type': 'configuration', 'description': 'Current selected data group, zero-indexed'},
                 {'length': 80, 'type': 'measurement', 'description': 'Array of 10 data groups. For each data group: 4 bytes mAh, 4 bytes mWh'},
                 {'length': 2, 'type': 'measurement', 'description': 'USB data line voltage (positive)'},
                 {'length': 2, 'type': 'measurement', 'description': 'USB data line voltage (negative)'},
                 {'length': 2, 'type': 'measurement', 'description': 'Charging mode index'},
                 {'length': 4, 'type': 'measurement', 'description': 'mAh from threshold-based recording'},
                 {'length': 4, 'type': 'measurement', 'description': 'mWh from threshold-based recording'},
                 {'length': 2, 'type': 'configuration', 'description': 'Currently configured amperage for threshold recording'},
                 {'length': 4, 'type': 'measurement', 'description': 'Duration of threshold recording, in cumulative seconds'},
                 {'length': 2, 'type': 'configuration', 'description': 'Threshold recording active'},
                 {'length': 2, 'type': 'configuration', 'description': 'Current screen timeout setting, in minutes (0-9)'},
                 {'length': 2, 'type': 'configuration', 'description': 'Current backlight setting (0-5)'},
                 {'length': 4, 'type': 'measurement', 'description': 'Resistance'},
                 {'length': 2, 'type': 'configuration', 'description': 'Current screen'},
                 {'length': 1, 'type': 'unknown', 'description': 'Unknown'},
                 {'length': 1, 'type': 'checksum/unknown', 'description': 'Checksum or unknown'},
                 ]


KNOWN_DEVICES = {'0963': 'UM24C', '09c9': 'UM25C', '0d4c': 'UM34C'}


CHARGING_MODES = [{'value': 'UNKNOWN', 'description': 'Charging mode: Unknown, or normal (non-custom mode)'},
                      {'value': 'QC2', 'description': 'Charging mode: Qualcomm Quick Charge 2.0'},
                      {'value': 'QC3', 'description': 'Charging mode: Qualcomm Quick Charge 3.0'},
                      {'value': 'APP2.4A', 'description': 'Charging mode: Apple, max 2.4 Amp'},
                      {'value': 'APP2.1A', 'description': 'Charging mode: Apple, max 2.4 Amp'},
                      {'value': 'APP1.0A', 'description': 'Charging mode: Apple, max 2.4 Amp'},
                      {'value': 'APP0.5A', 'description': 'Charging mode: Apple, max 2.4 Amp'},
                      {'value': 'DCP1.5A', 'description': 'Charging mode: Dedicated Charging Port, max 1.5 Amp (D+ to D- short'},
                      {'value': 'SAMSUNG', 'description': 'Charging mode: Samsung (Adaptive Fast Charging'},
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


class UM34CResponseBase(BaseModel):
    type: Union[str, None] = None
    description: Union[str, None] = None
    byte_offset: Union[int, None] = None
    byte_length: Union[int, None] = None
    value_unit: Union[str, None] = None


class UM34CResponseGroupDataRaw(BaseModel):
    mAh: Union[str, None] = None
    mWh: Union[str, None] = None


class UM34CResponseGroupData(BaseModel):
    mAh: Union[float, None] = None
    mWh: Union[float, None] = None


class UM34CResponseDatapointStr(UM34CResponseBase):
    value_type = 'string'
    value: Union[str, None] = None


class UM34CResponseDatapointInt(UM34CResponseBase):
    value_type = 'integer'
    value: Union[int, None] = None
    value_unit = '1'


class UM34CResponseDatapointFloat(UM34CResponseBase):
    value_type = 'float'
    value: Union[float, None] = None
    value_unit = '1'


class UM34CResponseDatapointBool(UM34CResponseBase):
    value_type = 'bool'
    value: Union[bool, None] = None


class UM34CResponseDatapointList(UM34CResponseBase):
    value_type = 'array'
    value: Union[List[UM34CResponseGroupData], None] = None


class UM34CResponseDatapointListRaw(UM34CResponseBase):
    value_type = 'array'
    value: Union[List[UM34CResponseGroupDataRaw], None] = None


class UM34CResponseData(BaseModel):
    model_id: Union[UM34CResponseDatapointStr, None] = None
    voltage: Union[UM34CResponseDatapointFloat, None] = None
    amperage: Union[UM34CResponseDatapointFloat, None] = None
    wattage: Union[UM34CResponseDatapointFloat, None] = None
    temperature_c: Union[UM34CResponseDatapointInt, None] = None
    temperature_f: Union[UM34CResponseDatapointInt, None] = None
    selected_group: Union[UM34CResponseDatapointInt, None] = None
    group_data: Union[UM34CResponseDatapointList, None] = None
    usb_volt_pos: Union[UM34CResponseDatapointFloat, None] = None
    usb_volt_neg: Union[UM34CResponseDatapointFloat, None] = None
    charging_mode: Union[UM34CResponseDatapointStr, None] = None
    thresh_mah: Union[UM34CResponseDatapointInt, None] = None
    thresh_mwh: Union[UM34CResponseDatapointInt, None] = None
    thresh_amps: Union[UM34CResponseDatapointFloat, None] = None
    thresh_seconds: Union[UM34CResponseDatapointInt, None] = None
    thresh_active: Union[UM34CResponseDatapointBool, None] = None
    screen_timeout: Union[UM34CResponseDatapointInt, None] = None
    screen_backlight: Union[UM34CResponseDatapointInt, None] = None
    resistance: Union[UM34CResponseDatapointFloat, None] = None
    cur_screen: Union[UM34CResponseDatapointInt, None] = None


class UM34CResponseDataRaw(BaseModel):
    model_id: Union[UM34CResponseDatapointStr, None] = None
    voltage: Union[UM34CResponseDatapointStr, None] = None
    amperage: Union[UM34CResponseDatapointStr, None] = None
    wattage: Union[UM34CResponseDatapointStr, None] = None
    temperature_c: Union[UM34CResponseDatapointStr, None] = None
    temperature_f: Union[UM34CResponseDatapointStr, None] = None
    selected_group: Union[UM34CResponseDatapointStr, None] = None
    group_data: Union[UM34CResponseDatapointListRaw, None] = None
    usb_volt_pos: Union[UM34CResponseDatapointStr, None] = None
    usb_volt_neg: Union[UM34CResponseDatapointStr, None] = None
    charging_mode: Union[UM34CResponseDatapointStr, None] = None
    thresh_mah: Union[UM34CResponseDatapointStr, None] = None
    thresh_mwh: Union[UM34CResponseDatapointStr, None] = None
    thresh_amps: Union[UM34CResponseDatapointStr, None] = None
    thresh_seconds: Union[UM34CResponseDatapointStr, None] = None
    thresh_active: Union[UM34CResponseDatapointStr, None] = None
    screen_timeout: Union[UM34CResponseDatapointStr, None] = None
    screen_backlight: Union[UM34CResponseDatapointStr, None] = None
    resistance: Union[UM34CResponseDatapointStr, None] = None
    cur_screen: Union[UM34CResponseDatapointStr, None] = None


class UM34CResponse(CommandResponse):
    data: Union[List[UM34CResponseData], None] = None


class UM34CResponseRaw(CommandResponse):
    data: Union[List[UM34CResponseDataRaw], None] = None


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
    data[16]['value'] = [{'mAh': hex2int(x), 'mWh': hex2int(y)} for x, y in zip(data[16]['value'][0::2], data[16]['value'][1::2])]

    for k, divisor in zip([i for i in data.keys() if i not in [0, 16, 128, 129]], [100, 1000, 1000, 1, 1, 1, 100, 100, 1, 1, 1, 100, 1, 1, 1, 1, 10, 1]):
        data[k]['value'] = hex2int(data[k]['value'], divisor)
    data[100].update(CHARGING_MODES[data[100]['value']])
    data[116]['value'] = True if [data[116]['value']] == 1 else False

    units = {2: 'V', 4: 'A', 6: 'W', 10: 'C', 12: 'F', 16: 'mAh/mWh', 96: 'V', 98: 'V', 102: 'mAh', 106: 'mWh', 110: 'A', 112: 's', 118: 'min', 122: 'Ω'}
    for offset, unit in units.items():
        data[offset].update({'value_unit': unit})
    return data


def get_command_response(command: Enum, code: Union[bytes, None] = None) -> dict:
    code = command.value if code is None else code
    return {**BL_SOCK.get_info(), **{'command': command.name, 'command_code': '0' + str(code)[3:-1]}}


def add2hex(hex_val: bytes, add: int) -> bytes:
    val = int(hex_val.hex(), 16) + add
    return bytes.fromhex(hex(val)[2:])


def get_model_keys(model) -> list:
    return list(model.schema()['properties'])


@router.get('/request_data_raw', response_model=UM34CResponseRaw)
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

    #response = {**get_command_response(UM34CCommands.request_data), 'data': [{'offset': k, **v} for k, v in response.items()]}



    response_new = {}
    for key, (k, v) in zip(get_model_keys(UM34CResponseDataRaw), response.items()):
        response_new[key] = {'byte_offset': k, **v, 'byte_length': v['length']}

    response = {**{'timestamp': datetime.now()},
                **get_command_response(UM34CCommands.request_data),
                'data': [response_new]}
    print(response)
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

    response_new = {}
    for key, (k, v) in zip(get_model_keys(UM34CResponseData), response.items()):
        response_new[key] = {'byte_offset': k, **v, 'byte_length': v['length']}

    response = {**{'timestamp': datetime.now()},
                **get_command_response(UM34CCommands.request_data),
                'data': [response_new]}
    return response


@router.get('/next_screen', response_model=CommandResponse)
async def next_screen():
    """
    Go to next screen
    """
    BL_SOCK.send(command=UM34CCommands.next_screen.value)
    return {**{'timestamp': datetime.now()}, **get_command_response(command=UM34CCommands.next_screen)}


@router.get('/rotate_screen', response_model=CommandResponse)
async def rotate_screen(no_of_time: int = Query(default=1, description='How often it should rotate', ge=1, le=3)):
    """
    Rotate screen
    """
    for i in range(no_of_time):
        BL_SOCK.send(command=UM34CCommands.rotate_screen.value)
        if no_of_time > 1:
            time.sleep(0.9)
    return {**{'timestamp': datetime.now()}, **get_command_response(command=UM34CCommands.rotate_screen)}


@router.get('/previous_screen', response_model=CommandResponse)
async def previous_screen():
    """
    Go to previous screen
    """
    BL_SOCK.send(command=UM34CCommands.previous_screen.value)
    return {**{'timestamp': datetime.now()}, **get_command_response(command=UM34CCommands.previous_screen)}


@router.get('/clear_data_group', response_model=CommandResponse)
async def clear_data_group(group_no: Union[int, None] = Query(default=None, description='Number of group to delete data (optional)', ge=0, le=9)):
    """
    Delete data of current selected group

    If group number is given, the device will first switch to the group and then delete its data
    - without group number 🠖 current selected group data will be deleted
    - group_no = 1 🠖 select group number 1 then delete its data
    - group_no = 9 🠖 select group number 9 then delete its data
    """
    code = UM34CCommands.clear_data_group.value
    if group_no is not None:
        code = add2hex(UM34CCommands.select_group.value, group_no)
        BL_SOCK.send(command=code)
        time.sleep(0.03)
    BL_SOCK.send(command=UM34CCommands.clear_data_group.value)
    return {**{'timestamp': datetime.now()}, **get_command_response(command=UM34CCommands.clear_data_group, code=code)}


@router.get('/select_data_group', response_model=CommandResponse)
async def select_data_group(group_no: int = Query(default=Required, description='Group number to switch to', ge=0, le=9)):
    """
    Set the selected data group between 0 and 9
    - 0 = set selected group to 0
    - 7 = set selected group to 7
    """
    code = add2hex(UM34CCommands.select_group.value, group_no)
    BL_SOCK.send(command=code)
    return {**{'timestamp': datetime.now()}, **get_command_response(command=UM34CCommands.select_group, code=code)}


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
    return {**{'timestamp': datetime.now()}, **get_command_response(command=UM34CCommands.recording_threshold, code=code)}


@router.get('/set_backlight_level', response_model=CommandResponse)
async def set_backlight_level(level: int = Query(default=Required, description='Device backlight level', ge=0, le=5)):
    """
    Set device backlight level between 0 and 5 (inclusive)
    - 0 = dim
    - 5 = full brightness
    """
    code = add2hex(UM34CCommands.backlight_level.value, level)
    BL_SOCK.send(command=code)
    return {**{'timestamp': datetime.now()}, **get_command_response(command=UM34CCommands.backlight_level, code=code)}


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
    return {**{'timestamp': datetime.now()}, **get_command_response(command=UM34CCommands.screen_timeout, code=code)}


@router.get('/set_screen', response_model=CommandResponse)
async def set_screen(no: int = Query(default=Required, description='Number of screen to go to', ge=0, le=5)):
    """
    Go to a specific screen (0 - 5)
    - 0 = go to most left screen
    - 3 = go to screen number 3
    - 5 = go to most right screen

    Uses the next/previous screen command multiple times to go to the selected screen
    """
    data = BL_SOCK.send_and_receive(command=UM34CCommands.request_data.value)
    response = data_preperation_raw(datastring=data)
    cur_screen = int(response[126]['value'])
    diff = no - cur_screen
    if diff != 0:
        command = UM34CCommands.next_screen if diff > 0 else UM34CCommands.previous_screen
        for i in range(abs(diff)-1):
            BL_SOCK.send(command=command.value)
            time.sleep(0.3)
        BL_SOCK.send(command=command.value)
        return {**{'timestamp': datetime.now()}, **get_command_response(command=command)}
    else:
        return {**{'timestamp': datetime.now()}, **BL_SOCK.get_info(), **{'command': None, 'command_code': None}}


@router.get('/reset_device', response_model=CommandResponse)
async def reset_device():
    """
    Resetting the device
    - set screen to the most left one
    - delete data of all groups
    - set backlight to level 5
    - set screen timeout to 1 minute
    """
    data = BL_SOCK.send_and_receive(command=UM34CCommands.request_data.value)
    response = data_preperation_raw(datastring=data)
    cur_screen = int(response[126]['value'])
    diff = 0 - cur_screen
    if diff != 0:
        command = UM34CCommands.next_screen if diff > 0 else UM34CCommands.previous_screen
        for i in range(abs(diff)-1):
            BL_SOCK.send(command=command.value)
            time.sleep(0.3)
        BL_SOCK.send(command=command.value)

    for group_no in range(10):
        code = add2hex(UM34CCommands.select_group.value, group_no)
        BL_SOCK.send(command=code)
        time.sleep(0.05)
        BL_SOCK.send(command=UM34CCommands.clear_data_group.value)
        time.sleep(0.3)
    BL_SOCK.send(command=UM34CCommands.select_group.value)

    code = add2hex(UM34CCommands.backlight_level.value, 5)
    BL_SOCK.send(command=code)

    code = add2hex(UM34CCommands.screen_timeout.value, 1)
    BL_SOCK.send(command=code)

    return {**{'timestamp': datetime.now()}, **BL_SOCK.get_info(), **{'command': None, 'command_code': None}}

#TODO reset device

#TODO request_data --> get specific data


