import streamlit as st
import requests
from enum import Enum
import json

request_session = requests.Session()
request_session.trust_env = False

st.set_page_config(
    page_title='UM34C Dashboard',
    page_icon='',
    layout='wide'
)


def valid_ipv4_addr(ip: str):
    pairs = ip.split('.')
    if len(pairs) != 4:
        return False
    if not all(0 <= int(p) < 255 for p in pairs):
        return False
    if any(p.startswith('0') and p != '0' for p in pairs):
        return False
    return True


st.sidebar.markdown('# API Setting')
ip = st.sidebar.text_input('IPv4 address:', value="192.168.0.2", max_chars=15)
VALID_IP = valid_ipv4_addr(ip)
if not VALID_IP:
    st.sidebar.error("Not valid IPv4 address!")
port = st.sidebar.text_input('Port:', value="8080", max_chars=4)

base_url = f"http://{ip}:{port}/"


class UM34CApiCommand(Enum):
    __Bluetooth__ = ''
    discover_devices = base_url + 'bluetooth/discover_devices'
    connection_test = base_url + 'bluetooth/test'
    read_cache = base_url + 'bluetooth/cache'
    __Command__ = ''
    request_data_raw = base_url + 'command/' 'request_data_raw'
    request_data_raw_key = base_url + 'command/' 'request_data_raw'
    request_data = base_url + 'command/' 'request_data'
    request_data_key = base_url + 'command/' 'request_data'
    request_data_values = base_url + 'command/' 'request_data?value_only=true'
    next_screen = base_url + 'command/' 'next_screen'
    rotate_screen = base_url + 'command/' 'rotate_screen'
    previous_screen = base_url + 'command/' 'previous_screen'
    clear_data_group = base_url + 'command/' 'clear_data_group'
    select_data_group = base_url + 'command/' 'select_data_group'
    set_recording_threshold = base_url + 'command/' 'set_recording_threshold'
    set_backlight_level = base_url + 'command/' 'set_backlight_level'
    set_screen_timeout = base_url + 'command/' 'set_screen_timeout'
    set_screen = base_url + 'command/' 'set_screen'
    reset_device = base_url + 'command/''reset_device'
    send_response_to_db = base_url + 'command/''send_response_to_db'
    send_response_to_db_loop = base_url + 'command/''send_response_to_db_loop'
    stop_sending_loop = base_url + 'command/''stop_sending_loop'


def get_api_response(url: str):
    with section_response.container():
        req = request_session.get(url=url)
        content = req.content.decode('utf-8')
        content_json = json.loads(content)

        st.write(req)
        st.write(content_json)
        st.markdown(f"### Process-time\n{req.headers['x-process-time']} [s]")


section_buttons, section_response = st.columns(2)
with section_buttons.container():
    st.markdown('# API commands')
    tag = st.selectbox('Choose command', UM34CApiCommand.__members__.keys())
    data_vals = ['model_id', 'voltage', 'amperage', 'wattage', 'temperature_c', 'temperature_f', 'selected_group',
                 'group_data', 'usb_volt_pos', 'usb_volt_neg', 'charging_mode', 'thresh_mah', 'thresh_mwh',
                 'thresh_amps', 'thresh_seconds', 'thresh_active', 'screen_timeout', 'screen_backlight', 'resistance',
                 'cur_screen']

    selectionbox_vals = {
        'rotate_screen': {'label': 'How often rotate?', 'options': range(1, 4)},
        'clear_data_group': {'label': 'Which data group? (Optional)', 'options': ['-'] + list(range(0, 10))},
        'select_data_group': {'label': 'Which data group?', 'options': range(0, 10)},
        'set_recording_threshold': {'label': 'Which threshold?', 'options': range(0, 31)},
        'set_backlight_level': {'label': 'Which backlight level?', 'options': range(0, 6)},
        'set_screen_timeout': {'label': 'How many minutes?', 'options': range(0, 10)},
        'set_screen': {'label': 'Which screen?', 'options': range(0, 6)},
    }

    url = UM34CApiCommand[tag].value
    if tag in ['discover_devices', 'connection_test', 'read_cache']:
        st.markdown('## Bluetooth')

    elif tag in ['next_screen', 'previous_screen', 'reset_device']:
        st.markdown(f'## Command')

    elif tag in ['rotate_screen', 'clear_data_group', 'select_data_group', 'set_recording_threshold', 'set_backlight_level', 'set_screen_timeout', 'set_screen']:
        st.markdown('## Command')
        key = st.selectbox(selectionbox_vals[tag]['label'], selectionbox_vals[tag]['options'])
        if tag == 'rotate_screen':
            url += f'?no_of_time={key}'
        elif tag == 'clear_data_group':
            if key != '-':
                url += f'?group_no={key}'
        else:
            url += f'/{key}'

    elif tag.startswith('request'):
        st.markdown('## Command')
        if tag.endswith('key'):
            key = st.selectbox('Which data to request?', data_vals)
            url += f'/{key}'
        else:
            keys = st.multiselect("Which data to request?", data_vals)
            if keys:
                url += '?'
                for key in keys:
                    url += f'keys={key}&'
                url = url[:-1]
        vals_only = st.selectbox('Only contain values?', [False, True])
        if vals_only:
            url += '?' if url.find('?') == -1 else '&'
            url += f'values_only=true'
    st.button('Use command', on_click=lambda: get_api_response(url), disabled=not VALID_IP)


with section_response.container():
    st.markdown('# API response')
    st.markdown(url)

