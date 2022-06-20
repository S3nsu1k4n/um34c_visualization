from fastapi import HTTPException, status, Path, Query
from typing import Union, List
from .commands_models import UM34CResponseKeys, UM34Examples


async def verify_key_allowed(key: str = Path(default=None,
                                             description='Filter data by key',
                                             min_length=7,
                                             max_length=16,
                                             examples=UM34Examples.request_data_key
                                             )):
    if key in UM34CResponseKeys.schema()['properties'].keys():
        return key
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Given key '" + str(key) + "' does not exist in data",
                            headers={'X-Error': "Given key '" + str(key) + "' does not exist in data"}
                            )


async def verify_keys_allowed(keys: Union[List[str], None] = Query(default=None,
                                                                   description='Filter data by keys',
                                                                   examples=UM34Examples.request_data_q
                                                                   )):
    if keys is not None:
        return [await verify_key_allowed(key) for key in keys]
    else:
        return keys
