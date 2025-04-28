import streamlit as st

from st_screen_stats import ScreenData
from ui.vars import SCREEN_DATA, DATA_LABELING, DASHBOARD, SETTINGS


def set_screen_data_component():
    """Used to get screen info, e.g., the height and width."""
    screen_data = ScreenData(setTimeout=100)
    screen_data.st_screen_data(key=SCREEN_DATA)


def get_page_height(subtract: int):
    """Get the page height, subtracting a specific amount of pixels. If not set yet, return a default value of 500."""
    try:
        return st.session_state[SCREEN_DATA]['innerHeight'] - subtract
    except Exception as e:
        return 500


def remove_top_margin(page: str):
    """Remove the top margin of a page"""
    page_margins = {
        DATA_LABELING: -120,
        DASHBOARD: -120,
        SETTINGS: -120,
    }
    st.html(
        f"""
            <style>
                .stAppViewContainer .stMain .stMainBlockContainer {{
                    margin-top: {page_margins[page]}px;
                }}
            </style>"""
    )


def remove_header():
    """Remove Streamlit's header (and footer)"""
    st.markdown(
        """
            <style>
                header {
                    visibility: hidden;
                    height: 0%;
                }
                footer {
                    visibility: hidden;
                    height: 0%;
                }
            </style>
            """,
        unsafe_allow_html=True
    )