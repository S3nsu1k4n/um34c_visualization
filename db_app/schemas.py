from pydantic import BaseModel
from datetime import datetime
from typing import List


class GroupData(BaseModel):
    mah: int
    mwh: int


class UM34CResponse(BaseModel):
    created_at: datetime
    bd_address: str
    model_id: str
    voltage: float
    amperage: float
    wattage: float
    temperature_c: int
    temperature_f: int
    selected_group: int
    group_data: List[GroupData]
    usb_volt_pos: float
    usb_volt_neg: float
    charging_mode: str
    thresh_mah: int
    thresh_mwh: int
    thresh_amps: float
    thresh_seconds: int
    thresh_active: bool
    screen_timeout: int
    screen_backlight: int
    resistance: float
    cur_screen: int


class DeviceBase(BaseModel):
    bd_address: str
    model_id: str


class DeviceCreate(DeviceBase):
    pass


class Device(DeviceBase):
    class Config:
        orm_mode = True


class MeasurementBase(BaseModel):
    bd_address: str
    created_at: datetime
    voltage: float
    amperage: float
    wattage: float
    temperature_c: float
    temperature_f: float
    usb_volt_pos: float
    usb_volt_neg: float
    charging_mode: str
    thresh_mah: int
    thresh_mwh: int
    thresh_seconds: int
    resistance: float
    group0_mah: int
    group0_mwh: int
    group1_mah: int
    group1_mwh: int
    group2_mah: int
    group2_mwh: int
    group3_mah: int
    group3_mwh: int
    group4_mah: int
    group4_mwh: int
    group5_mah: int
    group5_mwh: int
    group6_mah: int
    group6_mwh: int
    group7_mah: int
    group7_mwh: int
    group8_mah: int
    group8_mwh: int
    group9_mah: int
    group9_mwh: int


class MeasurementCreate(MeasurementBase):
    pass


class Measurement(MeasurementBase):
    id: int

    class Config:
        orm_mode = True


class ConfigurationBase(BaseModel):
    bd_address: str
    created_at: datetime
    selected_group: int
    thresh_amps: float
    thresh_active: bool
    screen_timeout: int
    screen_backlight: int
    cur_screen: int


class ConfigurationCreate(ConfigurationBase):
    pass


class Configuration(ConfigurationBase):

    class Config:
        orm_mode = True
        

class CreateDataResponse(BaseModel):
    created_id: int
