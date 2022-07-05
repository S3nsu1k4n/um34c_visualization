import platform
import subprocess

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import FileResponse
from datetime import datetime
from typing import Union, List
import socket
from .commands_models import BLDeviceBase, BLDevice, BLErrorMessage400, BLErrorMessage404, BLErrorMessage409
from config import BluetoothSettings


PYBLUEZ_OK = False
AF_BLUETOOTH_OK = False
BLUETOOTH_TOOLS_OK = False
try:
    import bluetooth
    PYBLUEZ_OK = True
except ModuleNotFoundError:
    PYBLUEZ_OK = False


if platform.system() == 'Windows':
    socket.AF_BLUETOOTH
    try:
        a = subprocess.Popen("btinfo", stdout=subprocess.PIPE)
        BLUETOOTH_TOOLS_OK = True
    except FileNotFoundError:
        BLUETOOTH_TOOLS_OK = False


router = APIRouter(
    prefix='/bluetooth',
    tags=['bluetooth'],
    dependencies=[],
    responses={}
)

device_cache = dict()


# Dependency
def get_bluetooth_device():
    with BluetoothDevice(**BluetoothSettings().dict()) as bl_device:
        yield bl_device


def discover_devices() -> List[BLDeviceBase]:
    found_devices = [BLDeviceBase(**{'bd_address': addr, 'name': name}) for addr, name in bluetooth.discover_devices(lookup_names=True)]
    device_cache.update({device.name: device.bd_address for device in found_devices})
    return found_devices


def discover_devices_win() -> List[BLDeviceBase]:
    """
    Need to install 'bluetooth command line tools' for windows
    --> https://bluetoothinstaller.com/bluetooth-command-line-tools
    """
    p = subprocess.Popen("btdiscovery", stdout=subprocess.PIPE).communicate()[0].decode('utf-8').split('\n')[:-1]
    devices = [device.replace('\r', '').replace('(', '').replace(')', '').split('\t')[:2] for device in p]
    found_devices = [BLDeviceBase(**{'bd_address': addr, 'name': name}) for addr, name in devices]
    device_cache.update({device.name: device.bd_address for device in found_devices})
    return found_devices


class BluetoothDevice:
    def __init__(self, name: Union[str, None], bd_address: Union[str, None], bl_channel: int = 1, max_attempts: int = 10, attempts_delay: int = 5000):
        if PYBLUEZ_OK:
            self.sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        else:
            self.sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)

        self.device_name = name if name else None
        self.bd_address = bd_address.replace('_', ':') if bd_address else None
        self.channel = int(bl_channel)
        self.max_attempts = int(max_attempts)
        self.attempts_delay = int(attempts_delay)

        if self.bd_address is None:
            self.findout_bd_address()

        if self.device_name is None and BLUETOOTH_TOOLS_OK:
            self.get_name_by_addr()

        self.check_address_valid()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.sock.close()

    def findout_bd_address(self):
        if self.device_name in device_cache:
            self.bd_address = device_cache[self.device_name]
        else:
            discover_devices() if PYBLUEZ_OK else discover_devices_win() if BLUETOOTH_TOOLS_OK else None
            if self.device_name in device_cache:
                self.bd_address = device_cache[self.device_name]
            else:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail=f"No device found named {self.device_name}",
                                    headers={'X-Error': f"No device found named {self.device_name}"}
                                    )

    def get_name_by_addr(self):
        for i in range(2):
            for name, bd_address in device_cache.items():
                if self.bd_address == bd_address:
                    self.device_name = name
                    return
            discover_devices_win()

    def is_valid_address(self):
        """returns True if address is a valid Bluetooth address.

        valid address are always strings of the form XX:XX:XX:XX:XX:XX
        where X is a hexadecimal character.  For example,
        01:23:45:67:89:AB is a valid address, but IN:VA:LI:DA:DD:RE is not.

        --> From PyBluez library
        """
        try:
            pairs = self.bd_address.split(":")
            if len(pairs) != 6: return False
            if not all(0 <= int(b, 16) <= 255 for b in pairs): return False
        except:
            return False
        return True

    def check_address_valid(self):
        if PYBLUEZ_OK:
            if not bluetooth.is_valid_address(self.bd_address):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                        detail=f"Invalid address: {self.bd_address}",
                                        headers={'X-Error': f"Invalid address: {self.bd_address}"}
                                        )
        else:
            if not self.is_valid_address():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=f"Invalid address: {self.bd_address}",
                                    headers={'X-Error': f"Invalid address: {self.bd_address}"}
                                    )

    def get_bd_address(self) -> str:
        return self.bd_address

    def get_name(self) -> str:
        return self.device_name

    def get_channel(self) -> int:
        return self.channel

    def connect(self) -> dict:
        attempts = 0

        while attempts <= self.max_attempts:
            if PYBLUEZ_OK:
                self.sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            else:
                self.sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            try:
                self.sock.connect((self.bd_address, self.channel))
                if PYBLUEZ_OK:
                    self.device_name = bluetooth.lookup_name(self.bd_address)
                break
            except TimeoutError:
                raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT,
                                    detail='Timeout',
                                    headers={'X-Error': 'Timeout'}
                                    )
            except OSError as e:
                pass
            except IOError as error:
                pass
            finally:
                attempts += 1

        else:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail='Too many attempts',
                                headers={'X-Error': 'Too many attempts'}
                                )

        return {'timestamp': datetime.now(), 'name': self.device_name, 'bd_address': self.bd_address, 'channel': self.channel}

    def send(self, command: bytes) -> None:
        self.sock.send(command)

    def send_and_receive(self, command: bytes) -> str:
        self.sock.send(command)
        buffer = bytearray()
        while len(buffer) < 130:
            buffer += self.sock.recv(130)
        return buffer.hex()

    def get_info(self):
        return {'name': self.get_name(), 'bd_address': self.get_bd_address(), 'channel': self.get_channel()}


@router.get('/', include_in_schema=False)
async def bl_index():
    return FileResponse('./app/static/templates/bluetooth_index.html')


@router.get('/discover_devices', response_model=List[BLDeviceBase], response_model_exclude_unset=True,
            status_code=200,
            summary='Get a list of nearby bluetooth devices',
            response_description='List of nearby devices',
            deprecated=not PYBLUEZ_OK and not BLUETOOTH_TOOLS_OK)
async def get_nearby_devices():
    """
    Searches for nearby bluetooth devices

    Found devices will be saved in cache

    **INFO** : Will only work if pybluez is installed! Or 'Bluetooth Command Line Tools' is installed on Windows!
    """
    if PYBLUEZ_OK:
        return discover_devices()
    elif BLUETOOTH_TOOLS_OK:
        return discover_devices_win()


@router.get('/test', response_model=BLDevice,
                     summary='Tests connection and get infos about the connected bluetooth device',
                     response_description='Infos about the connected bluetooth device',
                     responses={400: {'model': BLErrorMessage400},
                                404: {'model': BLErrorMessage404},
                                409: {'model': BLErrorMessage409}}
)
async def test(bl_sock=Depends(get_bluetooth_device)):
    """
    Test connection and get infos about the
    connected bluetooth device
    """
    return {'timestamp': datetime.now(),
            'name': bl_sock.get_name(),
            'bd_address': bl_sock.get_bd_address(),
            'channel': bl_sock.get_channel()
            }


@router.get('/cache', response_model=List[BLDeviceBase],
                      summary='Shows cached bluetooth devices',
                      response_description='List of cached devices',
)
async def get_device_cache():
    """
    Shows cached bluetooth devices. Every time 'device_discovery' is used, the found devices and its bd address will be saved.

    Device discovery will be used when:
    - any device command is used and a name but no bd_address is given. Or opposite.
    - user uses the '/discover_devices' command
    """
    return [{'name': name, 'bd_address': bd_address} for name, bd_address in device_cache.items()]
