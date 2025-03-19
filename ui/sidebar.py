import streamlit_antd_components as sac


def sidebar_menu():
    page = sac.menu([
        sac.MenuItem('Data Cleaning', icon='tags'),
        sac.MenuItem('Dashboard', icon='bar-chart'),
        sac.MenuItem('Settings', icon='gear'),
    ], open_all=True)
    return page
