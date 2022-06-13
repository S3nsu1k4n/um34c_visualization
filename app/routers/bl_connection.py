from fastapi import APIRouter, HTTPException, status, Query, Path
from fastapi.responses import FileResponse
from datetime import datetime
from typing import Union
import socket

from .commands_models import BLDevice
from config import UM34CConfig


router = APIRouter(
    prefix='/bluetooth',
    tags=['bluetooth'],
    dependencies=[],
    responses={}
)


class BluetoothConnection:
    def __init__(self):
        self.sock: Union[socket.socket, None] = None
        self.device_name: Union[str, None] = None
        self.bd_address: Union[str, None] = None
        self.port: Union[int, None] = None
        self.attempts = 0

    def __enter__(self):
        self.sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.sock is not None:
            self.sock.close()

    def get_sock(self) -> Union[socket.socket, None]:
        return self.sock

    def get_bd_address(self) -> Union[int, None]:
        return self.bd_address

    def get_port(self) -> Union[int, None]:
        return self.port

    def get_info(self) -> dict:
        return {'name': self.device_name, 'bd_address': self.bd_address, 'port': self.port}

    def set_name(self, name: str) -> None:
        self.device_name = name

    def reset(self) -> None:
        self.sock = None
        self.bd_address = None
        self.port = None
        self.attempts = 0

    def connect(self, bd_address: str, port: int) -> dict:
        self.bd_address = bd_address
        self.port = port
        self.sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        #self.sock.settimeout(int(UM34CConfig.ATTEMPT_DELAY.value)/1000)
        self.attempts = 0

        if self.attempts <= int(UM34CConfig.MAX_ATTEMPTS.value) or self.bd_address is not self.port:
            try:
                self.sock.connect((self.bd_address, self.port))
            except TimeoutError:
                self.sock.close()
                raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT,
                                    detail='Timeout',
                                    headers={'X-Error': 'Timeout'}
                                    )
            except OSError:
                self.sock.close()
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail='Problem to connect to device by bluetooth',
                                    headers={'X-Error': 'Problem to connect to device by bluetooth'}
                                    )

        else:
            self.sock.close()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail='Too many attempts',
                                headers={'X-Error': 'Too many attempts'}
                                )
        known_devices = {'0963': 'UM24C', '09c9': 'UM25C', '0d4c': 'UM34C'}
        device_name = self.send_and_receive(b'\xf0')[:4]
        self.device_name = known_devices[device_name]

        return {'timestamp': datetime.now(), 'name': self.device_name, 'bd_address': self.bd_address, 'port': self.port}

    def disconnect(self) -> None:
        self.sock.close()

    def send(self, command: bytes) -> None:
        if self.sock is None:
            raise HTTPException(status_code=status.HTTP_418_IM_A_TEAPOT,
                                detail='Not connected with bluetooth device',
                                headers={'X-Error': 'Not connected with device'}
                                )
        self.sock.send(command)

    def send_and_receive(self, command: bytes) -> str:
        if self.sock is None:
            raise HTTPException(status_code=status.HTTP_418_IM_A_TEAPOT,
                                detail='Not connected with bluetooth device',
                                headers={'X-Error': 'Not connected with device'}
                                )
        self.sock.send(command)
        data = ''
        data_size = 0
        while data_size < 130:
            payload = self.sock.recv(131)
            data += payload.hex()
            data_size += len(payload)
        return data


BL_SOCK = BluetoothConnection()


@router.get('/', include_in_schema=False)
async def bl_index():
    return FileResponse('./app/static/templates/bluetooth_index.html')


@router.get('/connect_by_bd_address/{bd_address}', response_model=BLDevice,
            status_code=status.HTTP_201_CREATED,
            summary='Connect with bluetooth by bd_address',
            response_description='Successfully connected via bluetooth'
            )
async def connect_by_address(bd_address: str = Path(default=UM34CConfig.BD_ADDRESS.value, description='Bluetooth Device Address to connect to', max_length=17, min_length=17),
                             port: int = Query(default=1, description='Port number of bluetooth connection', ge=1, le=30)):
    """
    Connect to the device with the specified bd_address:

    - **bd_addr**: The Bluetooth Device Address to connect to
    - possible to use **_** instead of **:**
    """
    bd_address = bd_address.replace('_', ':')
    print('Connecting with', bd_address)
    BL_SOCK.reset()
    response = BL_SOCK.connect(bd_address=bd_address, port=port)

    return response


@router.get('/disconnect')
async def disconnect() -> None:
    BL_SOCK.disconnect()
