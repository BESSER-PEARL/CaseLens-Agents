import sys
# sys.path.append("/Path/to/directory/agentic-framework") # Replace with your directory path

import streamlit as st
from streamlit.runtime import Runtime
from streamlit.web import cli as stcli


from agents.data_labeling_agent.data_labeling_agent import data_labeling_agent
from agents.data_labeling_agent.data_labeling_ui import data_labeling
from app.initialization import initialize
from app.sidebar import sidebar_menu
from app.vars import DATA_LABELING

st.set_page_config(layout="wide")


@st.cache_resource
def run_agents():
    # TODO: Agents in another docker container
    data_labeling_agent.run(sleep=False)
    return True


if __name__ == "__main__":
    if st.runtime.exists():
        run_agents()
        initialize()
        with st.sidebar:
            page = sidebar_menu()
        if page == DATA_LABELING:
            data_labeling()
    else:
        sys.argv = ["streamlit", "run", sys.argv[0]]
        sys.exit(stcli.main())
