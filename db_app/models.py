from sqlalchemy import (
    Boolean, Column, ForeignKey, Integer, String, Float, DateTime
)
from sqlalchemy.orm import relationship

from database import Base

class Device(Base):
    __tablename__ = 'devices'
    bd_address = Column(String, primary_key=True, unique=True, index=True)
    model_id = Column(String, index=True)

    measurements = relationship('Measurement', back_populates='device')
    configuration = relationship('Configuration', back_populates='device')


class Measurement(Base):
    __tablename__ = 'measurement'

    id = Column(Integer, primary_key=True, index=True)
    bd_address = Column(Integer, ForeignKey('devices.bd_address'))

    created_at = Column(DateTime, index=True)
    voltage = Column(Float, index=True)
    amperage = Column(Float, index=True)
    wattage = Column(Float, index=True)
    temperature_c = Column(Integer, index=True)
    temperature_f = Column(Integer, index=True)
    usb_volt_pos = Column(Float, index=True)
    usb_volt_neg = Column(Float, index=True)
    charging_mode = Column(String, index=True)
    thresh_mah = Column(Integer, index=True)
    thresh_mwh = Column(Integer, index=True)
    thresh_seconds = Column(Integer, index=True)
    resistance = Column(Float, index=True)
    group0_mah = Column(Integer, index=True)
    group0_mwh = Column(Integer, index=True)
    group1_mah = Column(Integer, index=True)
    group1_mwh = Column(Integer, index=True)
    group2_mah = Column(Integer, index=True)
    group2_mwh = Column(Integer, index=True)
    group3_mah = Column(Integer, index=True)
    group3_mwh = Column(Integer, index=True)
    group4_mah = Column(Integer, index=True)
    group4_mwh = Column(Integer, index=True)
    group5_mah = Column(Integer, index=True)
    group5_mwh = Column(Integer, index=True)
    group6_mah = Column(Integer, index=True)
    group6_mwh = Column(Integer, index=True)
    group7_mah = Column(Integer, index=True)
    group7_mwh = Column(Integer, index=True)
    group8_mah = Column(Integer, index=True)
    group8_mwh = Column(Integer, index=True)
    group9_mah = Column(Integer, index=True)
    group9_mwh = Column(Integer, index=True)

    device = relationship('Device', back_populates='measurements')


class Configuration(Base):
    __tablename__ = 'configuration'

    id = Column(Integer, primary_key=True, index=True)
    bd_address = Column(Integer, ForeignKey('devices.bd_address'), unique=True, index=True)

    created_at = Column(DateTime, index=True)
    selected_group = Column(Integer, index=True)
    thresh_amps = Column(Float, index=True)
    thresh_active = Column(Boolean, index=True)
    screen_timeout = Column(Integer, index=True)
    screen_backlight = Column(Integer, index=True)
    cur_screen = Column(Integer, index=True)

    device = relationship('Device', back_populates='configuration')
