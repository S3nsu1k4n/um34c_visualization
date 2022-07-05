from enum import Enum


class Examples(Enum):
    post_data: dict = {
        'sample 1': {
            'summary': 'Something',
            'description': 'default example value',
            'value': {
                'created_at': '2022-06-10T13:54:19.972Z',
                'bd_address': '00:00:00:00:00:00',
                'model_id': 'UM34C',
                'voltage': 5.08,
                'amperage': 0.023,
                'wattage': 0.116,
                'temperature_c': 31,
                'temperature_f': 89,
                'selected_group': 0,
                'group_data': [{'mah': 0, 'mwh': 0},
                               {'mah': 1, 'mwh': 1},
                               {'mah': 2, 'mwh': 2},
                               {'mah': 3, 'mwh': 3},
                               {'mah': 4, 'mwh': 4},
                               {'mah': 5, 'mwh': 5},
                               {'mah': 6, 'mwh': 6},
                               {'mah': 7, 'mwh': 7},
                               {'mah': 8, 'mwh': 8},
                               {'mah': 9, 'mwh': 9},
                               ],
                'usb_volt_pos': 2.98,
                'usb_volt_neg': 0.04,
                'charging_mode': 'Unknown',
                'thresh_mah': 0,
                'thresh_mwh': 0,
                'thresh_amps': 0.3,
                'thresh_seconds': 0,
                'thresh_active': False,
                'screen_timeout': 0,
                'screen_backlight': 5,
                'resistance': 220.8,
                'cur_screen': 1
            },
        }
    }
