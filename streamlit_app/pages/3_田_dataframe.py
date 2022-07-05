import streamlit as st
import requests
import json
import pandas as pd
from io import BytesIO


request_session = requests.Session()
request_session.trust_env = False
st.set_page_config(
    page_title='Dataframe',
    page_icon='',
    layout='wide'
)
st.title('Dataframe')


def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    workbook = writer.book
    worksheet = writer.sheets['Sheet1']
    format1 = workbook.add_format({'num_format': '0.00'})
    worksheet.set_column('A:A', None, format1)
    writer.save()
    processed_data = output.getvalue()
    return processed_data


def put_api_setting():
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
    port = st.sidebar.text_input('Port:', value="8081", max_chars=4)
    try:
        hours = int(st.sidebar.text_input(label='hours', value=1, max_chars=2))
    except ValueError:
        hours = 1
    st.sidebar.markdown('# Device config')

    base_url = f"http://{ip}:{port}/"
    return base_url, VALID_IP, hours


def get_data_from_db(url: str):
    req = request_session.get(url=url)

    if req.status_code == 200:
        content = req.content
        content_json = json.loads(content)
        df = pd.DataFrame(content_json)
        try:
            id = df.pop('id')
            df.insert(0, 'id', id)
        except KeyError:
            pass

        datetime_df = df.pop('created_at')
        df['timestamp'] = pd.to_datetime(datetime_df)
        df = df.set_index('timestamp')
        return df
    else:
        return None


def groupby_hour(df):
    try:
        df.pop('id')
    except KeyError:
        pass
    group = df.resample('H').median()
    return group


def show_config(df: pd.DataFrame, placeholder: st.empty) -> None:
    with placeholder.container():
        for key in df.columns:
            st.markdown(f"{key}\n\n\t{df[key].max()}")


def init():
    base_url, valid_ip, hours = put_api_setting()
    df = get_data_from_db(base_url + f'data/measurements?hours={hours}')
    df_config = get_data_from_db(base_url + 'data/configurations')

    section_sidebar = st.sidebar.empty()
    show_config(df_config, section_sidebar)

    st.markdown('# Requested data')

    st.write(df)

    st.download_button(label='Download excel', data=to_excel(df), file_name='test.xlsx')

    st.markdown('# Data hourly (median)')
    df_hourly = groupby_hour(df)
    st.write(df_hourly)
    st.download_button(label='Download excel', data=to_excel(df_hourly), file_name='test.xlsx')


init()