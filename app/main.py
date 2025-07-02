import sys
# sys.path.append("/Path/to/directory/agentic-framework") # Replace with your directory path

import streamlit as st
from besser.agent.platforms.websocket import WEBSOCKET_PORT
from streamlit.runtime import Runtime
from streamlit.web import cli as stcli

from agents.chat_files_agent.chat_files_agent import chat_files_agent
from agents.chat_files_agent.chat_files_ui import chat_files
from agents.data_labeling_agent.data_labeling_agent import data_labeling_agent
from agents.data_labeling_agent.data_labeling_ui import data_labeling
from app.home import home
from app.initialization import initialize
from app.settings import settings
from app.sidebar import sidebar_menu
from app.vars import *

st.set_page_config(layout="wide")


@st.cache_resource
def run_agents():
    # TODO: Agents in another docker container
    data_labeling_agent.set_property(WEBSOCKET_PORT, 8765)
    data_labeling_agent.run(sleep=False)
    chat_files_agent.set_property(WEBSOCKET_PORT, 8766)
    chat_files_agent.run(sleep=False)
    return True


if __name__ == "__main__":
    if st.runtime.exists():
        run_agents()
        initialize()
        with st.sidebar:
            page = sidebar_menu()
        if page == HOME:
            home()
        if page == DATA_LABELING:
            data_labeling()
        elif page == CHAT_FILES:
            chat_files()
        elif page == SETTINGS:
            settings()
    else:
        sys.argv = ["streamlit", "run", sys.argv[0]]
        sys.exit(stcli.main())
