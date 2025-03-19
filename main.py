import sys
# sys.path.append("/Path/to/directory/agentic-framework") # Replace with your directory path

import streamlit as st
from streamlit.runtime import Runtime
from streamlit.web import cli as stcli


from agent import agent
from ui.initialization import initialize
from ui.pages.data_cleaning import data_cleaning
from ui.sidebar import sidebar_menu

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
