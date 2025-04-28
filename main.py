import sys
# sys.path.append("/Path/to/directory/agentic-framework") # Replace with your directory path

import streamlit as st
from streamlit.runtime import Runtime
from streamlit.web import cli as stcli


from agent import agent
from ui.initialization import initialize
from ui.pages.data_labeling import data_labeling
from ui.sidebar import sidebar_menu
from ui.utils import set_screen_data_component, remove_top_margin, remove_header
from ui.vars import DATA_LABELING

st.set_page_config(layout="wide")


@st.cache_resource
def run_agent():
    # TODO: Agent in another docker container
    agent.run(sleep=False)
    return True


if __name__ == "__main__":
    if st.runtime.exists():
        set_screen_data_component()
        run_agent()
        initialize()
        with st.sidebar:
            page = sidebar_menu()
        # Remove top margin
        remove_top_margin(page)
        # Remove Streamlit's header
        remove_header()
        if page == DATA_LABELING:
            data_labeling()
    else:
        sys.argv = ["streamlit", "run", sys.argv[0]]
        sys.exit(stcli.main())
