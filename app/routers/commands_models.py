from pydantic import BaseModel, Field
from enum import Enum
from typing import Union, List
from datetime import datetime


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


class BLDevice(BaseModel):
    timestamp: datetime
    name: Union[str, None] = None
    bd_address: Union[str, None] = Field(default=None, title='bd_address', min_length=17, max_length=17)
    port: Union[int, None] = Field(default=None)


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
