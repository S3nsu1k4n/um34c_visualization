from typing import List

from fastapi import Depends, FastAPI, Body
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .database import SessionLocal, engine
from .examples import Examples

models.Base.metadata.create_all(bind=engine)


app = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post('/data/')
def create_data(response: schemas.UM34CResponse = Body(examples=Examples.post_data), db: Session = Depends(get_db)):
    return crud.create_measurement_and_configuration(db=db, response=response)


@app.get('/data/devices', response_model=List[schemas.Device])
def get_devices(db: Session = Depends(get_db)):
    return crud.get_all_devices(db)


@app.get('/data/configurations', response_model=List[schemas.Configuration])
def get_configurations(db: Session = Depends(get_db)):
    return crud.get_all_configurations(db)


@app.get('/data/measurements', response_model=List[schemas.Measurement])
def get_measurements(db: Session = Depends(get_db)):
    return crud.get_all_measurements(db)