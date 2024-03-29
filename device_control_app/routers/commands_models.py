from pydantic import BaseModel, Field
from enum import Enum
from typing import Union, List
from datetime import datetime
from config import BluetoothSettings


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


CHARGING_MODES = [{'value': 'Unknown', 'description': 'Charging mode: Unknown, or normal (non-custom mode)'},
                      {'value': 'QC2', 'description': 'Charging mode: Qualcomm Quick Charge 2.0'},
                      {'value': 'QC3', 'description': 'Charging mode: Qualcomm Quick Charge 3.0'},
                      {'value': 'APP2.4A', 'description': 'Charging mode: Apple, max 2.4 Amp'},
                      {'value': 'APP2.1A', 'description': 'Charging mode: Apple, max 2.4 Amp'},
                      {'value': 'APP1.0A', 'description': 'Charging mode: Apple, max 2.4 Amp'},
                      {'value': 'APP0.5A', 'description': 'Charging mode: Apple, max 2.4 Amp'},
                      {'value': 'DCP1.5A', 'description': 'Charging mode: Dedicated Charging Port, max 1.5 Amp (D+ to D- short'},
                      {'value': 'SAMSUNG', 'description': 'Charging mode: Samsung (Adaptive Fast Charging'},
                  ]


class BLDeviceBase(BaseModel):
    name: Union[str, None] = Field(default=None, example='UM34C')
    bd_address: Union[str, None] = Field(default=None, title='bd_address', min_length=17, max_length=17, example='aa:bb:cc:dd:ee:ff')


class BLDevice(BLDeviceBase):
    timestamp: Union[datetime, None] = Field(default=None, example=datetime.now())
    channel: Union[int, None] = Field(default=None, example=1)


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
    command: Union[str, None] = Field(title='Used command', example='0xf0')
    command_code: Union[str, None] = Field(title='Code of used command', example=UM34CCommands.request_data.name)


class UM34CResponseBase(BaseModel):
    type: Union[str, None] = Field(default=None, example='measurement')
    description: Union[str, None] = Field(default=None, example='Current measured voltage')
    byte_offset: Union[int, None] = Field(default=None, example=116)
    byte_length: Union[int, None] = Field(default=None, example=2)
    value_unit: Union[str, None] = Field(default=None, example='V')


class UM34CResponseGroupDataRaw(BaseModel):
    mah: Union[str, None] = None
    mwh: Union[str, None] = None


class UM34CResponseGroupData(BaseModel):
    mah: Union[int, None] = Field(default=None, example=23)
    mwh: Union[int, None] = Field(default=None, example=116)


class UM34CResponseDatapointStr(UM34CResponseBase):
    value_type: str = Field(default='string')
    value: Union[str, None] = Field(default=None, example='UM34C')


class UM34CResponseDatapointInt(UM34CResponseBase):
    value_type: str = Field(default='integer')
    value: Union[int, None] = Field(default=None, example=33)
    value_unit = '1'


class UM34CResponseDatapointFloat(UM34CResponseBase):
    value_type: str = Field(default='float')
    value: Union[float, None] = Field(default=None, example=220.8)
    value_unit = '1'


class UM34CResponseDatapointBool(UM34CResponseBase):
    value_type: str = Field(default='bool')
    value: Union[bool, None] = Field(default=None, example=False)
    value_unit = 'true/false'


class UM34CResponseDatapointList(UM34CResponseBase):
    value_type: str = Field(default='array')
    value: Union[List[UM34CResponseGroupData], None] = Field(default=None, example=[{"mAh": 23,"mWh": 116},{"mAh": 0,"mWh": 0}])
    value_unit = 'mah/mwh'


class UM34CResponseDatapointListRaw(UM34CResponseBase):
    value_type: str = Field(default='array')
    value: Union[List[UM34CResponseGroupDataRaw], None] = None
    value_unit = 'mah/mwh'


class UM34CResponseData(BaseModel):
    model_id: Union[UM34CResponseDatapointStr, None] = Field(default=None, example={"type":"model","description":"Model ID","byte_offset":0,"byte_length":2,"value":"UM34C"})
    voltage: Union[UM34CResponseDatapointFloat, None] = Field(default=None, example={"type":"measurement","description":"Current measured voltage","byte_offset":2,"byte_length":2,"value_unit":"V","value":5.08})
    amperage: Union[UM34CResponseDatapointFloat, None] = Field(default=None, example={"type":"measurement","description":"Current measured amperage","byte_offset":4,"byte_length":2,"value_unit":"A","value":0.023})
    wattage: Union[UM34CResponseDatapointFloat, None] = Field(default=None, example={"type":"measurement","description":"Current measured wattage","byte_offset":6,"byte_length":4,"value_unit":"W","value":0.116})
    temperature_c: Union[UM34CResponseDatapointInt, None] = Field(default=None, example={"type":"measurement","description":"Current measured temperature Celsius","byte_offset":10,"byte_length":2,"value_unit":"C","value":33})
    temperature_f: Union[UM34CResponseDatapointInt, None] = Field(default=None, example={"type":"measurement","description":"Current measured temperature Fahrenheit","byte_offset":12,"byte_length":2,"value_unit":"F","value":92})
    selected_group: Union[UM34CResponseDatapointInt, None] = Field(default=None, example={"type":"configuration","description":"Current selected datagroup, zero-indexed","byte_offset":14,"byte_length":2,"value":0})
    group_data: Union[UM34CResponseDatapointList, None] = Field(default=None, example={"type":"measurement","description":"Array of 10 data groups. For each data group: 4 bytes mAh, 4 bytes mWh","byte_offset":16,"byte_length":80,"value_unit": "mAh/mWh","value": [{"mAh":28,"mWh":145},{"mAh":0,"mWh":0}, {"mAh":0,"mWh":0},{"mAh":0,"mWh":0},{"mAh":0,"mWh":0},{"mAh":0,"mWh":0},{"mAh":0,"mWh":0},{"mAh":0,"mWh":0},{"mAh":0,"mWh":0},{"mAh":0,"mWh":0}]})
    usb_volt_pos: Union[UM34CResponseDatapointFloat, None] = Field(default=None, example={"type":"measurement","description":"USB dataline voltage (positive)","byte_offset":96,"byte_length":2,"value_unit":"V","value":2.89})
    usb_volt_neg: Union[UM34CResponseDatapointFloat, None] = Field(default=None, example={"type":"measurement","description":"USB dataline voltage (negative)","byte_offset":98,"byte_length":2,"value_unit":"V","value":0.03})
    charging_mode: Union[UM34CResponseDatapointStr, None] = Field(default=None, example={"type":"measurement","description":"Charging mode: Unknown, or normal (non-custommode)","byte_offset":100,"byte_length":2,"value":"UNKNOWN"})
    thresh_mah: Union[UM34CResponseDatapointInt, None] = Field(default=None, example={"type":"measurement","description":"mAh from threshold-based recording","byte_offset":102,"byte_length":4,"value_unit":"mAh","value":0})
    thresh_mwh: Union[UM34CResponseDatapointInt, None] = Field(default=None, example={"type":"measurement","description":"mWh from threshold-based recording","byte_offset":106,"byte_length":4,"value_unit":"mWh","value":0})
    thresh_amps: Union[UM34CResponseDatapointFloat, None] = Field(default=None, example={"type":"configuration","description":"Currently configured amperage for threshold recording","byte_offset":110,"byte_length":2,"value_unit":"A","value":0.3})
    thresh_seconds: Union[UM34CResponseDatapointInt, None] = Field(default=None, example={"type":"measurement","description":"Duration of threshold recording,in cumulative seconds","byte_offset":112,"byte_length":4,"value_unit":"s","value":0})
    thresh_active: Union[UM34CResponseDatapointBool, None] = Field(default=None, example={"type":"configuration","description":"Threshold recording active","byte_offset":116,"byte_length":2,"value":False})
    screen_timeout: Union[UM34CResponseDatapointInt, None] = Field(default=None, example={"type":"configuration","description":"Current screen timeout setting,in minutes (0-9)","byte_offset":118,"byte_length":2,"value_unit":"min","value":0})
    screen_backlight: Union[UM34CResponseDatapointInt, None] = Field(default=None, example={"type":"configuration","description":"Current backlight setting (0-5)","byte_offset":120,"byte_length":2,"value":5})
    resistance: Union[UM34CResponseDatapointFloat, None] = Field(default=None, example={"type":"measurement","description":"Resistance","byte_offset":122,"byte_length":4,"value_unit":"Ω","value":220.8})
    cur_screen: Union[UM34CResponseDatapointInt, None] = Field(default=None, example={"type":"configuration","description":"Current screen","byte_offset":126,"byte_length":2,"value":0})


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

    class Config:
        schema_extra = {
            'example': {
              "name": "UM34C",
              "channel": 1,
              "command": "request_data",
              "command_code": "0xf0",
              "data": [
                {
                  "model_id": {
                    "type": "model",
                    "description": "Model ID",
                    "byte_offset": 0,
                    "byte_length": 2,
                    "value": "0d4c"
                  },
                  "voltage": {
                    "type": "measurement",
                    "description": "Current measured voltage",
                    "byte_offset": 2,
                    "byte_length": 2,
                    "value": "01fc"
                  },
                  "amperage": {
                    "type": "measurement",
                    "description": "Current measured amperage",
                    "byte_offset": 4,
                    "byte_length": 2,
                    "value": "0017"
                  },
                  "wattage": {
                    "type": "measurement",
                    "description": "Current measured wattage",
                    "byte_offset": 6,
                    "byte_length": 4,
                    "value": "00000074"
                  },
                  "temperature_c": {
                    "type": "measurement",
                    "description": "Current measured temperature Celsius",
                    "byte_offset": 10,
                    "byte_length": 2,
                    "value": "0021"
                  },
                  "temperature_f": {
                    "type": "measurement",
                    "description": "Current measured temperature Fahrenheit",
                    "byte_offset": 12,
                    "byte_length": 2,
                    "value": "005c"
                  },
                  "selected_group": {
                    "type": "configuration",
                    "description": "Current selected data group, zero-indexed",
                    "byte_offset": 14,
                    "byte_length": 2,
                    "value": "0000"
                  },
                  "group_data": {
                    "type": "configuration",
                    "description": "Array of 10 data groups. For each data group: 4 bytes mAh, 4 bytes mWh",
                    "byte_offset": 16,
                    "byte_length": 80,
                    "value": [
                      {
                        "mAh": "00000022",
                        "mWh": "000000ad"
                      },
                      {
                        "mAh": "00000000",
                        "mWh": "00000000"
                      },
                      {
                        "mAh": "00000000",
                        "mWh": "00000000"
                      },
                      {
                        "mAh": "00000000",
                        "mWh": "00000000"
                      },
                      {
                        "mAh": "00000000",
                        "mWh": "00000000"
                      },
                      {
                        "mAh": "00000000",
                        "mWh": "00000000"
                      },
                      {
                        "mAh": "00000000",
                        "mWh": "00000000"
                      },
                      {
                        "mAh": "00000000",
                        "mWh": "00000000"
                      },
                      {
                        "mAh": "00000000",
                        "mWh": "00000000"
                      },
                      {
                        "mAh": "00000000",
                        "mWh": "00000000"
                      }
                    ]
                  },
                  "usb_volt_pos": {
                    "type": "measurement",
                    "description": "USB data line voltage (positive)",
                    "byte_offset": 96,
                    "byte_length": 2,
                    "value": "0121"
                  },
                  "usb_volt_neg": {
                    "type": "measurement",
                    "description": "USB data line voltage (negative)",
                    "byte_offset": 98,
                    "byte_length": 2,
                    "value": "0001"
                  },
                  "charging_mode": {
                    "type": "measurement",
                    "description": "Charging mode index",
                    "byte_offset": 100,
                    "byte_length": 2,
                    "value": "0000"
                  },
                  "thresh_mah": {
                    "type": "measurement",
                    "description": "mAh from threshold-based recording",
                    "byte_offset": 102,
                    "byte_length": 4,
                    "value": "00000000"
                  },
                  "thresh_mwh": {
                    "type": "measurement",
                    "description": "mWh from threshold-based recording",
                    "byte_offset": 106,
                    "byte_length": 4,
                    "value": "00000000"
                  },
                  "thresh_amps": {
                    "type": "configuration",
                    "description": "Currently configured amperage for threshold recording",
                    "byte_offset": 110,
                    "byte_length": 2,
                    "value": "001e"
                  },
                  "thresh_seconds": {
                    "type": "measurement",
                    "description": "Duration of threshold recording, in cumulative seconds",
                    "byte_offset": 112,
                    "byte_length": 4,
                    "value": "00000000"
                  },
                  "thresh_active": {
                    "type": "configuration",
                    "description": "Threshold recording active",
                    "byte_offset": 116,
                    "byte_length": 2,
                    "value": "0000"
                  },
                  "screen_timeout": {
                    "type": "configuration",
                    "description": "Current screen timeout setting, in minutes (0-9)",
                    "byte_offset": 118,
                    "byte_length": 2,
                    "value": "0000"
                  },
                  "screen_backlight": {
                    "type": "configuration",
                    "description": "Current backlight setting (0-5)",
                    "byte_offset": 120,
                    "byte_length": 2,
                    "value": "0005"
                  },
                  "resistance": {
                    "type": "measurement",
                    "description": "Resistance",
                    "byte_offset": 122,
                    "byte_length": 4,
                    "value": "000008a0"
                  },
                  "cur_screen": {
                    "type": "configuration",
                    "description": "Current screen",
                    "byte_offset": 126,
                    "byte_length": 2,
                    "value": "0000"
                  }
                }
              ]
            }
        }


class UM34CResponseKeys(BaseModel):
    model_id = 'model_id'
    voltage = 'voltage'
    amperage = 'amperage'
    wattage = 'wattage'
    temperature_c = 'temperature_c'
    temperature_f = 'temperature_f'
    selected_group = 'selected_group'
    group_data = 'group_data'
    usb_volt_pos = 'usb_volt_pos'
    usb_volt_neg = 'usb_volt_neg'
    charging_mode = 'charging_mode'
    thresh_mah = 'thresh_mah'
    thresh_mwh = 'thresh_mwh'
    thresh_amps = 'thresh_amps'
    thresh_seconds = 'thresh_seconds'
    thresh_active = 'thresh_active'
    screen_timeout = 'screen_timeout'
    screen_backlight = 'screen_backlight'
    resistance = 'resistance'
    cur_screen = 'cur_screen'


class UM34Examples(Enum):
    request_data_key: dict = {'default': {'description': 'default example value', 'value': None},
                              'Model ID': {'description': 'Get name of device', 'value': 'model_id'},
                              'Voltage': {'description': 'Get current measured voltage', 'value': 'voltage'},
                              'Amperage': {'description': 'Get current measured amperage', 'value': 'amperage'},
                              'Wattage': {'description': 'Get current measured wattage', 'value': 'wattage'},
                              'Temperature in Celsius': {'description': 'Get current measured temperature in celsius', 'value': 'temperature_c'},
                              'Temperature in Fahrenheit': {'description': 'Get current measured temperature in fahrenheit', 'value': 'temperature_f'},
                              'Selected group': {'description': 'Get selected group', 'value': 'selected_group'},
                              'Group data': {'description': 'Get data from groups', 'value': 'group_data'},
                              'USB voltage +': {'description': 'Get current measured USB data line voltage (positive)', 'value': 'usb_volt_pos'},
                              'USB voltage -': {'description': 'Get current measured USB data line voltage (negative)', 'value': 'usb_volt_neg'},
                              'Charging mode': {'description': 'Get charging mode', 'value': 'charging_mode'},
                              'Threshold mAh': {'description': 'Get mAh from threshold-based recording', 'value': 'thresh_mah'},
                              'Threshold mWh': {'description': 'Get mWh from threshold-based recording', 'value': 'thresh_mwh'},
                              'Thresh amperage': {'description': 'Get configured amperage for threshold recording', 'value': 'thresh_amps'},
                              'Thresh seconds': {'description': 'Get duration of threshold recording, in cumulative seconds', 'value': 'thresh_seconds'},
                              'Thresh active': {'description': 'Get threshold recording active', 'value': 'thresh_active'},
                              'Screen timeout': {'description': 'Get current screen timeout setting, in minutes (0-9)', 'value': 'screen_timeout'},
                              'Screen backlight': {'description': 'Get Current backlight setting (0-5)', 'value': 'screen_backlight'},
                              'Resistance': {'description': 'Get current measured resistance', 'value': 'resistance'},
                              'Current Screen': {'description': 'Get current screen', 'value': 'cur_screen'},
                              }
    request_data_q: dict = {'default': {'description': 'default example value', 'value': None},
                            'Model ID': {'description': 'Get name of device', 'value': ['model_id']},
                            'Group data': {'description': 'Get only group data','value': ['selected_group', 'group_data']},
                            'Threshold data': {'description': 'Get only threshold data','value': ['thresh_mah', 'thresh_mwh', 'thresh_amps', 'thresh_seconds', 'thresh_active']},
                            'Measurement data': {'description': 'Get only measurement data', 'value': ['voltage', 'amperage', 'wattage', 'temperature_c', 'temperature_f', 'group_data', 'charging_mode', 'usb_volt_pos', 'usb_volt_neg', 'thresh_mah','thresh_mwh', 'thresh_seconds', 'resistance']},
                            'Configuration data': {'description': 'Get only configuration data','value': ['selected_group', 'thresh_amps', 'thresh_active', 'screen_timeout', 'screen_backlight', 'cur_screen']},
                            }
    bd_address: dict = {'default': {'description': 'default example value', 'value': None}, 'From configuration': {'description': 'Use bd address from configuration', 'value': BluetoothSettings().bd_address},}
    device_names: dict = {'default': {'description': 'default example value', 'value': None},
                          'Device name is UM24C': {'description': 'Use the name of the device', 'value': 'UM24C'},
                          'Device name is UM25C': {'description': 'Use the name of the device', 'value': 'UM25C'},
                          'Device name is UM34C': {'description': 'Use the name of the device', 'value': 'UM34C'},
                          }

    max_attempts: dict = {'default': {'description': 'default example value', 'value': 10}, 'From configuration': {'description': 'Use max attempts from configuration', 'value': BluetoothSettings().max_attempts}, }
    attempt_delay: dict = {'default': {'description': 'default example value', 'value': 5000}, 'From configuration': {'description': 'Use attempt delay from configuration', 'value': BluetoothSettings().attempts_delay}, }
    clear_data_group: dict = {'default (Delete current group data)': {'description': 'default example value (delete current selected group)', 'value': None},
                              'Delete group 0 data': {'description': 'Select group 0 and delete its data', 'value': 0},
                              'Delete group 1 data': {'description': 'Select group 1 and delete its data', 'value': 1},
                              'Delete group 2 data': {'description': 'Select group 2 and delete its data', 'value': 2},
                              'Delete group 3 data': {'description': 'Select group 3 and delete its data', 'value': 3},
                              'Delete group 4 data': {'description': 'Select group 4 and delete its data', 'value': 4},
                              'Delete group 5 data': {'description': 'Select group 5 and delete its data', 'value': 5},
                              'Delete group 6 data': {'description': 'Select group 6 and delete its data', 'value': 6},
                              'Delete group 7 data': {'description': 'Select group 7 and delete its data', 'value': 7},
                              'Delete group 8 data': {'description': 'Select group 8 and delete its data', 'value': 8},
                              'Delete group 9 data': {'description': 'Select group 9 and delete its data', 'value': 9}
                              }
    select_data_group: dict = {'default': {'description': 'default example value', 'value': None},
                               'Select group 0': {'description': 'Select group 0', 'value': 0},
                               'Select group 1': {'description': 'Select group 1', 'value': 1},
                               'Select group 2': {'description': 'Select group 2', 'value': 2},
                               'Select group 3': {'description': 'Select group 3', 'value': 3},
                               'Select group 4': {'description': 'Select group 4', 'value': 4},
                               'Select group 5': {'description': 'Select group 5', 'value': 5},
                               'Select group 6': {'description': 'Select group 6', 'value': 6},
                               'Select group 7': {'description': 'Select group 7', 'value': 7},
                               'Select group 8': {'description': 'Select group 8', 'value': 8},
                               'Select group 9': {'description': 'Select group 9', 'value': 9},
                               }
    set_recording_threshold: dict = {'default': {'description': 'default example value', 'value': None},
                                     'Set threshold to 0.00 A': {'description': 'Sets threshold to 0.00 A', 'value': 0},
                                     'Set threshold to 0.01 A': {'description': 'Sets threshold to 0.01 A', 'value': 1},
                                     'Set threshold to 0.02 A': {'description': 'Sets threshold to 0.02 A', 'value': 2},
                                     'Set threshold to 0.03 A': {'description': 'Sets threshold to 0.03 A', 'value': 3},
                                     'Set threshold to 0.04 A': {'description': 'Sets threshold to 0.04 A', 'value': 4},
                                     'Set threshold to 0.05 A': {'description': 'Sets threshold to 0.05 A', 'value': 5},
                                     'Set threshold to 0.06 A': {'description': 'Sets threshold to 0.06 A', 'value': 6},
                                     'Set threshold to 0.07 A': {'description': 'Sets threshold to 0.07 A', 'value': 7},
                                     'Set threshold to 0.08 A': {'description': 'Sets threshold to 0.08 A', 'value': 8},
                                     'Set threshold to 0.09 A': {'description': 'Sets threshold to 0.09 A', 'value': 9},
                                     'Set threshold to 0.10 A': {'description': 'Sets threshold to 0.10 A', 'value': 10},
                                     'Set threshold to 0.11 A': {'description': 'Sets threshold to 0.11 A', 'value': 11},
                                     'Set threshold to 0.12 A': {'description': 'Sets threshold to 0.12 A', 'value': 12},
                                     'Set threshold to 0.13 A': {'description': 'Sets threshold to 0.13 A', 'value': 13},
                                     'Set threshold to 0.14 A': {'description': 'Sets threshold to 0.14 A', 'value': 14},
                                     'Set threshold to 0.15 A': {'description': 'Sets threshold to 0.15 A', 'value': 15},
                                     'Set threshold to 0.16 A': {'description': 'Sets threshold to 0.16 A', 'value': 16},
                                     'Set threshold to 0.17 A': {'description': 'Sets threshold to 0.17 A', 'value': 17},
                                     'Set threshold to 0.18 A': {'description': 'Sets threshold to 0.18 A', 'value': 18},
                                     'Set threshold to 0.19 A': {'description': 'Sets threshold to 0.19 A', 'value': 19},
                                     'Set threshold to 0.20 A': {'description': 'Sets threshold to 0.20 A', 'value': 20},
                                     'Set threshold to 0.21 A': {'description': 'Sets threshold to 0.21 A', 'value': 21},
                                     'Set threshold to 0.22 A': {'description': 'Sets threshold to 0.22 A', 'value': 22},
                                     'Set threshold to 0.23 A': {'description': 'Sets threshold to 0.23 A', 'value': 23},
                                     'Set threshold to 0.24 A': {'description': 'Sets threshold to 0.24 A', 'value': 24},
                                     'Set threshold to 0.25 A': {'description': 'Sets threshold to 0.25 A', 'value': 25},
                                     'Set threshold to 0.26 A': {'description': 'Sets threshold to 0.26 A', 'value': 26},
                                     'Set threshold to 0.27 A': {'description': 'Sets threshold to 0.27 A', 'value': 27},
                                     'Set threshold to 0.28 A': {'description': 'Sets threshold to 0.28 A', 'value': 28},
                                     'Set threshold to 0.29 A': {'description': 'Sets threshold to 0.29 A', 'value': 29},
                                     'Set threshold to 0.30 A': {'description': 'Sets threshold to 0.30 A', 'value': 30},
                                     }
    set_backlight: dict = {'default': {'description': 'default example value', 'value': None},
                           'level 0 (dim)': {'description': 'Sets backlight level to 0', 'value': 0},
                           'level 1': {'description': 'Sets backlight level to 1', 'value': 1},
                           'level 2': {'description': 'Sets backlight level to 2', 'value': 2},
                           'level 3': {'description': 'Sets backlight level to 3', 'value': 3},
                           'level 4': {'description': 'Sets backlight level to 4', 'value': 4},
                           'level 5 (full brightness)': {'description': 'Sets backlight level to 5', 'value': 5},
                           }
    set_screen_timeout: dict = {'default': {'description': 'default example value', 'value': None},
                                '0 minutes (no screensaver)': {'description': 'Sets screen timeout to 0', 'value': 0},
                                '1 minute': {'description': 'Sets screen timeout to 1 minute', 'value': 1},
                                '2 minutes': {'description': 'Sets screen timeout to 2 minutes', 'value': 2},
                                '3 minutes': {'description': 'Sets screen timeout to 3 minutes', 'value': 3},
                                '4 minutes': {'description': 'Sets screen timeout to 4 minutes', 'value': 4},
                                '5 minutes': {'description': 'Sets screen timeout to 5 minutes', 'value': 5},
                                '6 minutes': {'description': 'Sets screen timeout to 6 minutes', 'value': 6},
                                '7 minutes': {'description': 'Sets screen timeout to 7 minutes', 'value': 7},
                                '8 minutes': {'description': 'Sets screen timeout to 8 minutes', 'value': 8},
                                '9 minutes': {'description': 'Sets screen timeout to 9 minutes', 'value': 9},
                                }
    set_screen: dict = {'default': {'description': 'default example value', 'value': None},
                        'screen 0 (most left)': {'description': 'Go to screen 0 (most left)', 'value': 0},
                        'screen 1': {'description': 'Go to screen 1', 'value': 1},
                        'screen 2': {'description': 'Go to screen 2', 'value': 2},
                        'screen 3': {'description': 'Go to screen 3', 'value': 3},
                        'screen 4': {'description': 'Go to screen 4', 'value': 4},
                        'screen 5 (most right)': {'description': 'Go to screen 5 (most right)', 'value': 5},
                        }


class BLErrorMessage400(BaseModel):
    detail: str = "Invalid address: {bd_address}"


class BLErrorMessage404(BaseModel):
    detail: str ="No device found named {device_name}"


class BLErrorMessage409(BaseModel):
    detail: str ="Too many attempts"


class GroupData(BaseModel):
    mah: int
    mwh: int


class DBResponse(BaseModel):
  created_id: Union[int, None]
  message: Union[str, None]