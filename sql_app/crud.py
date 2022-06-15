from sqlalchemy.orm import Session

from . import models, schemas


def create_measurement_and_configuration(db: Session, response: schemas.UM34CResponse):
    data = response.dict()
    for i, val in enumerate(data['group_data']):
        data.update({'group'+str(i)+'_mah': val['mah']})
        data.update({'group'+str(i)+'_mwh': val['mwh']})
    create_device(db, schemas.DeviceCreate(**{key: data[key] for key in schemas.DeviceCreate.schema()['properties'].keys()}))
    create_measurement(db, schemas.MeasurementCreate(**{key: data[key] for key in schemas.MeasurementCreate.schema()['properties'].keys()}))
    create_configuration(db, schemas.ConfigurationCreate(**{key: data[key] for key in schemas.ConfigurationCreate.schema()['properties'].keys()}))


def get_all_devices(db: Session):
    return db.query(models.Device).offset(0).limit(5).all()


def get_all_configurations(db: Session):
    return db.query(models.Configuration).all()


def get_all_measurements(db: Session):
    return db.query(models.Measurement).all()


def create_device(db: Session, device: schemas.DeviceCreate):
    if device.bd_address not in [device.bd_address for device in get_all_devices(db)]:
        db_device_data = models.Device(**device.dict())
        db.add(db_device_data)
        db.commit()
        db.refresh(db_device_data)


def create_measurement(db: Session, measurement: schemas.MeasurementCreate):
    db_measurement_data = models.Measurement(**measurement.dict())
    db.add(db_measurement_data)
    db.commit()
    db.refresh(db_measurement_data)


def create_configuration(db: Session, configuration: schemas.ConfigurationCreate):
    if configuration.bd_address not in [configs.bd_address for configs in get_all_configurations(db)]:
        db_configuration_data = models.Configuration(**configuration.dict())
        db.add(db_configuration_data)
        db.commit()
        db.refresh(db_configuration_data)
    else:
        db.query(models.Configuration).filter(models.Configuration.bd_address == configuration.bd_address).update(configuration.dict(), synchronize_session="fetch")
        db.commit()
