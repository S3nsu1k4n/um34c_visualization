from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field, Required
from typing import Union, List
import socket
from config import UM34CConfig


router = APIRouter(
    prefix='/bl',
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
        # name, bd_address, port
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
        self.attempts = 0

        if self.attempts <= 5 or self.bd_address is not self.port:
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
                                    detail='No bluetooth device found',
                                    headers={'X-Error': 'No bluetooth device found'}
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

        return {'name': self.device_name, 'bd_address': self.bd_address, 'port': self.port}

    def disconnect(self) -> None:
        self.sock.close()

    def send(self, command: bytes) -> None:
        self.sock.send(command)

    def send_and_receive(self, command: bytes) -> str:
        self.sock.send(command)
        data = ''
        data_size = 0
        while data_size < 130:
            payload = self.sock.recv(131)
            data += payload.hex()
            data_size += len(payload)
        return data


BL_SOCK = BluetoothConnection()


class BLDevice(BaseModel):
    name: Union[str, None] = None
    bd_address: Union[str, None] = Field(default=None, title='bd_address', min_length=17, max_length=17)
    port: Union[int, None] = Field(default=None)


def search_nearby_devices():
    data = []
    for device in bluetooth.discover_devices(lookup_names=True):
        data.append({'name': device[1], 'bd_addr': device[0]})
    if len(data) == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='No bluetooth device found',
                            headers={'X-Error': 'No bluetooth device found'}
                            )
    return data


@router.get('/nearby', response_model=List[BLDevice])
async def get_nearby_devices():
    """
    Search nearby bluetooth devices and return a list of names and their adresses
    """
    return search_nearby_devices()


@router.get('/connect_by_devicename')
async def connect_by_devicename(device_name: str = Query(default=Required, description='Name of bluetooth device to connect to', max_length=32),
                                port: int = Query(default=1, description='Port number of bluetooth connection'),
                                ):
    """
    Connect to the device by its device name
    1. Step: Search nearby bluetooth devices
    2. Step: Check if device_name is found
    3. Step: Connect to the device with the found bd_address:

    - **device_name**: The name of the device to connect to via bluetooth
    """
    found_devices = search_nearby_devices()
    bd_address = None
    for device in found_devices:
        if device_name == device['name']:
            bd_address = device['bd_addr']
            print(bd_address)

    if bd_address is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Bluetooth address of '{device_name}' not found",
                            headers={'X-Error': f'Bluetooth address of "{device_name}" not found'}
                            )

    # TODO connect with found address
    print('FOUND', bd_address)


@router.get('/connect_by_bd_address')
async def connect_by_address(bd_address: str = Query(default=UM34CConfig.BD_ADDRESS.value, description='Bluetooth Device Address to connect to', max_length=17, min_length=17),
                             port: int = Query(default=1, description='Port number of bluetooth connection'),):
    """
    Connect to the device with the specified bd_address:

    - **bd_addr**: The Bluetooth Device Address to connect to
    """
    print('Connecting with', bd_address)
    # TODO connect with address
    BL_SOCK.reset()
    response = BL_SOCK.connect(bd_address=bd_address, port=port)

    return response


@router.get('/disconnect')
async def disconnect() -> None:
    BL_SOCK.disconnect()
