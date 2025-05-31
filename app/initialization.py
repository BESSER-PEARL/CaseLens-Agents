import queue
import sys
import threading

import streamlit as st
import websocket
from streamlit.runtime.scriptrunner_utils.script_run_context import add_script_run_ctx

from agents.data_labeling_agent.request import Instruction, Filter
from agents.utils.websocket_callbacks import on_open, on_error, on_message, on_close, on_ping, on_pong
from app.session_management import session_monitoring
from app.vars import *


def initialize():
    for i, agent_name in enumerate(AGENTS):
        if agent_name not in st.session_state:
            st.session_state[agent_name] = {}

        if SUBMIT_TEXT not in st.session_state[agent_name]:
            st.session_state[agent_name][SUBMIT_TEXT] = False

        if HISTORY not in st.session_state[agent_name]:
            st.session_state[agent_name][HISTORY] = []

        if QUEUE not in st.session_state[agent_name]:
            st.session_state[agent_name][QUEUE] = queue.Queue()

        if WEBSOCKET not in st.session_state[agent_name]:
            host = 'localhost'
            port = 8765 + i
            ws = websocket.WebSocketApp(f"ws://{host}:{port}/",
                                        on_open=on_open,
                                        on_message=on_message(agent_name),
                                        on_error=on_error,
                                        on_close=on_close,
                                        on_ping=on_ping,
                                        on_pong=on_pong)
            websocket_thread = threading.Thread(target=ws.run_forever)
            add_script_run_ctx(websocket_thread)
            websocket_thread.start()
            st.session_state[agent_name][AGENT_WEBSOCKET_PORT] = port
            st.session_state[agent_name][WEBSOCKET] = ws

    if SESSION_MONITORING not in st.session_state:
        session_monitoring_thread = threading.Thread(target=session_monitoring,
                                                     kwargs={'interval': SESSION_MONITORING_INTERVAL})
        add_script_run_ctx(session_monitoring_thread)
        session_monitoring_thread.start()
        st.session_state[SESSION_MONITORING] = session_monitoring_thread

    # Data labeling agent
    if FILTERS not in st.session_state[AGENT_DATA_LABELING]:
        st.session_state[AGENT_DATA_LABELING][FILTERS] = []
    if FILTERS_CHECKBOXES not in st.session_state[AGENT_DATA_LABELING]:
        st.session_state[AGENT_DATA_LABELING][FILTERS_CHECKBOXES] = []

    if INSTRUCTIONS not in st.session_state[AGENT_DATA_LABELING]:
        st.session_state[AGENT_DATA_LABELING][INSTRUCTIONS] = []
    if INSTRUCTIONS_CHECKBOXES not in st.session_state[AGENT_DATA_LABELING]:
        st.session_state[AGENT_DATA_LABELING][INSTRUCTIONS_CHECKBOXES] = []

    # Chat files agent
    if CHAT_PAGE not in st.session_state[AGENT_CHAT_FILES]:
        st.session_state[AGENT_CHAT_FILES][CHAT_PAGE] = 1

    if CHAT not in st.session_state[AGENT_CHAT_FILES]:
        st.session_state[AGENT_CHAT_FILES][CHAT] = None
