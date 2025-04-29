import streamlit as st
import streamlit_antd_components as sac
from app.vars import *


def sidebar_menu():
    page = sac.menu([
        sac.MenuItem(HOME, icon='house-fill'),
        sac.MenuItem('Agents', icon='robot', children=[
            sac.MenuItem(DATA_LABELING, icon='tags-fill'),
            sac.MenuItem(CHAT_FILES, icon='wechat'),
            sac.MenuItem(DASHBOARD, icon='bar-chart-fill'),
        ]),
        sac.MenuItem(SETTINGS, icon='gear-fill'),
    ], open_all=True)
    st.session_state[CURRENT_PAGE] = page
    return page
