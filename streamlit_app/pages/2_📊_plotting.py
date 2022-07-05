import pandas as pd
import plotly.express as px
import streamlit as st
import requests
import json
import time


request_session = requests.Session()
request_session.trust_env = False
st.set_page_config(
    page_title='Plotting',
    page_icon='',
    layout='wide'
)
st.title('Plotting')


labels = {
    'voltage': 'Voltage [V]',
    'amperage': 'Current [A]',
    'wattage': 'Power [W]',
    'temperature_c': 'Temperature [C]',
    'temperature_f': 'Temperature [F]',
    'usb_volt_pos': 'USB Voltage Positive [V]',
    'usb_volt_neg': 'USB Voltage Negative [V]',
    'thresh_mah': 'Treshold data [mAh]',
    'thresh_mwh': 'Treshold data [mWh]',
    'thresh_seconds': 'Treshold recording [s]',
    'resistance': 'Resistance [Ω]'
}
for i in range(10):
    labels.update({f'group{i}_mah': f'Group data {i} [mAh]'})
    labels.update({f'group{i}_mwh': f'Group data {i} [mWh]'})


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
    group = df.resample('H').median()
    return group


def plot_data(df, placeholder, data2show: str, data2show2: str):
    with placeholder.container():
        plot1, plot2 = st.columns(2)
        with plot1.container():
            fig = px.line(data_frame=df, y=df[data2show], x=df.index, labels={data2show: labels[data2show]})
            fig.update_layout(yaxis={"range": [0, df[data2show].max() * 1.1]})
            st.write(fig)
        with plot2.container():
            fig = px.line(data_frame=df, y=df[data2show2], x=df.index, labels={data2show2: labels[data2show2]})
            fig.update_layout(yaxis={"range": [0, df[data2show2].max() * 1.1]})
            st.write(fig)


def plot_data_hourly(df, placeholder, data2show: str, data2show2: str):
    with placeholder.container():
        plot1, plot2 = st.columns(2)
        with plot1.container():
            fig = px.bar(data_frame=df, y=df[data2show], x=df.index, labels={data2show: labels[data2show]})
            value = df[data2show].max()
            fig.update_layout(yaxis={"range": [0, value * 1.1]})
            fig.update_xaxes(tickformat='%H:%M', nticks=len(df)+2)
            st.write(fig)
        with plot2.container():
            fig = px.bar(data_frame=df, y=df[data2show2], x=df.index, labels={data2show2: labels[data2show2]})
            value = df[data2show2].max()
            fig.update_layout(yaxis={"range": [0, value * 1.1]})
            fig.update_xaxes(tickformat='%H:%M', nticks=len(df) + 2)
            st.write(fig)


def show_metrics(df: pd.DataFrame, placeholder: st.empty) -> None:
    with placeholder.container():
        timestamp = st.metric(label='Timestamp', value=str(df.index[-1])[:-7])
        labels = [['voltage', 'Voltage', 'V'], ['amperage', 'Current', 'A'], ['wattage', 'Power', 'W'], ['resistance', 'Resistance', 'Ω']]
        vals = st.columns(len(labels))
        df_grouped_h = groupby_hour(df)
        for val, labels in zip(vals, labels):
            value = df[labels[0]][-1]
            value_grouped = df_grouped_h[labels[0]][-1]
            val = val.metric(label=labels[1], value=f"{value} {labels[2]}", delta=round(value - value_grouped, 4))


def show_config(df: pd.DataFrame, placeholder: st.empty) -> None:
    with placeholder.container():
        for key in df.columns:
            st.markdown(f"{key}\n\n\t{df[key].max()}")


def init():
    base_url, valid_ip, hours = put_api_setting()
    loop = st.checkbox('Loop', disabled=not valid_ip)

    if loop:
        df = get_data_from_db(base_url + f'data/measurements?limit=100')
    else:
        df = get_data_from_db(base_url + f'data/measurements?hours={hours}')
    df_config = get_data_from_db(base_url + 'data/configurations')

    section_sidebar = st.sidebar.empty()

    section_metrics = st.empty()
    show_metrics(df, section_metrics)

    select, select2 = st.columns(2)
    df.pop('id')
    df.pop('bd_address')
    df.pop('charging_mode')
    with select.container():
        selected_measurement = st.selectbox('Which data to show in plot 1?', df.columns)
    with select2.container():
        selected_measurement2 = st.selectbox('Which data to show in plot 2?', df.columns)

    section_plot = st.empty()
    section_plot_hourly = st.empty()

    show_config(df_config, section_sidebar)

    update_time = 1
    while loop:
        start_time = time.time()

        # Update configurations
        df_config = get_data_from_db(base_url + 'data/configurations')
        show_config(df_config, section_sidebar)

        # Update metrics
        df = get_data_from_db(base_url + f'data/measurements?limit=100')
        show_metrics(df, section_metrics)

        # Update plot
        plot_data(df, placeholder=section_plot, data2show=selected_measurement, data2show2=selected_measurement2)
        plot_data_hourly(groupby_hour(df), placeholder=section_plot_hourly, data2show=selected_measurement, data2show2=selected_measurement2)

        t_delta = time.time() - start_time
        if update_time - t_delta > 0:
            time.sleep(update_time - t_delta)
    else:
        df = get_data_from_db(base_url + f'data/measurements?hours={hours}')
        plot_data(df, placeholder=section_plot, data2show=selected_measurement, data2show2=selected_measurement2)
        plot_data_hourly(groupby_hour(df), placeholder=section_plot_hourly, data2show=selected_measurement, data2show2=selected_measurement2)


init()