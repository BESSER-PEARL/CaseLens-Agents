import streamlit_antd_components as sac

from ui.vars import DATA_LABELING, DASHBOARD, SETTINGS


def sidebar_menu():
    page = sac.menu([
        sac.MenuItem(DATA_LABELING, icon='tags'),
        sac.MenuItem(DASHBOARD, icon='bar-chart'),
        sac.MenuItem(SETTINGS, icon='gear'),
    ], open_all=True)
    return page
