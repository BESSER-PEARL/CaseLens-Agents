import streamlit_antd_components as sac

from ui.vars import DATA_LABELING, DASHBOARD, SETTINGS, CHAT_FILES


def sidebar_menu():
    page = sac.menu([
        sac.MenuItem(DATA_LABELING, icon='tags-fill'),
        sac.MenuItem(CHAT_FILES, icon='wechat'),
        sac.MenuItem(DASHBOARD, icon='bar-chart-fill'),
        sac.MenuItem(SETTINGS, icon='gear-fill'),
    ], open_all=True)
    return page
