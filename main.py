import sys
# sys.path.append("/Path/to/directory/agentic-framework") # Replace with your directory path

import streamlit as st
from streamlit.runtime import Runtime
from streamlit.web import cli as stcli


from agent import agent
from streamlit_ui.chat import load_chat
from streamlit_ui.initialization import initialize
from streamlit_ui.message_input import message_input
from streamlit_ui.pages.data_cleaning import data_cleaning
from streamlit_ui.sidebar import sidebar, sidebar_menu

st.set_page_config(layout="wide")

@st.cache_resource
def run_agent():
    # TODO: Agent in another docker container
    agent.run(sleep=False)
    return True


if __name__ == "__main__":
    if st.runtime.exists():
        run_agent()
        initialize()
        with st.sidebar:
            page = sidebar_menu()
        if page == 'Data Cleaning':
            data_cleaning()
    else:
        sys.argv = ["streamlit", "run", sys.argv[0]]
        sys.exit(stcli.main())
