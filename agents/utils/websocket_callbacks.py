from __future__ import annotations

import ast
import base64
import json
from datetime import datetime
from io import StringIO

import numpy as np
import pandas as pd

from besser.agent.core.message import MessageType, Message
from besser.agent.exceptions.logger import logger
from besser.agent.platforms.payload import PayloadAction, Payload

from agents.chat_files_agent.notebook import add_notebook_find_topic_entry, add_notebook_hide_topic_entry
from app.session_management import get_streamlit_session
from app.vars import *

try:
    import cv2
except ImportError:
    logger.warning("cv2 dependencies in websocket_callbacks.py could not be imported. You can install them from "
                   "the requirements/requirements-extras.txt file")
try:
    import plotly
except ImportError:
    logger.warning("plotly dependencies in websocket_callbacks.py could not be imported. You can install them from "
                   "the requirements/requirements-extras.txt file")


def on_message(agent_name: str):

    def on_message_with_agent_name(ws, payload_str):
        # https://github.com/streamlit/streamlit/issues/2838
        streamlit_session = get_streamlit_session()
        payload: Payload = Payload.decode(payload_str)
        content = None
        if payload.action == PayloadAction.AGENT_REPLY_STR.value:
            try:
                content = json.loads(payload.message)
                # Get data for progress bar in data labeling agent
                if UPDATED_DOCS in content and IGNORED_DOCS in content and TOTAL_DOCS in content:
                    if PROGRESS_DATA_LABELING not in streamlit_session._session_state:
                        content[INITIAL_TIME] = datetime.now()
                    else:
                        content[INITIAL_TIME] = streamlit_session._session_state[PROGRESS_DATA_LABELING][INITIAL_TIME]
                    streamlit_session._session_state[PROGRESS_DATA_LABELING] = content
                    streamlit_session._handle_rerun_script_request()
                # Get data for progress bar in chat files agent
                if TOTAL_MESSAGES in content and PROCESSED_MESSAGES in content:
                    streamlit_session._session_state[PROGRESS_CHAT_FILES] = content
                    streamlit_session._handle_rerun_script_request()
                # Add entry to chat files notebook
                if TASK in content and CHAT_NAME in content and MESSAGE_IDS in content and TOPIC in content:
                    chat_name = content[CHAT_NAME]
                    message_ids = content[MESSAGE_IDS]
                    topic = content[TOPIC]
                    if content[TASK] == FIND_TOPIC:
                        add_notebook_find_topic_entry(chat_name=chat_name, topic=topic, message_ids=message_ids)
                    elif content[TASK] == HIDE_TOPIC:
                        add_notebook_hide_topic_entry(chat_name=chat_name, topic=topic, message_ids=message_ids)
                    streamlit_session._handle_rerun_script_request()
            except Exception:
                content = payload.message
                t = MessageType.STR
        elif payload.action == PayloadAction.AGENT_REPLY_MARKDOWN.value:
            content = payload.message
            t = MessageType.MARKDOWN
        elif payload.action == PayloadAction.AGENT_REPLY_HTML.value:
            content = payload.message
            t = MessageType.HTML
        elif payload.action == PayloadAction.AGENT_REPLY_FILE.value:
            content = payload.message
            t = MessageType.FILE
        elif payload.action == PayloadAction.AGENT_REPLY_IMAGE.value:
            decoded_data = base64.b64decode(payload.message)  # Decode base64 back to bytes
            np_data = np.frombuffer(decoded_data, np.uint8)  # Convert bytes to numpy array
            img = cv2.imdecode(np_data, cv2.IMREAD_COLOR)  # Decode numpy array back to image
            content = img
            t = MessageType.IMAGE
        elif payload.action == PayloadAction.AGENT_REPLY_DF.value:
            content = pd.read_json(StringIO(payload.message))
            t = MessageType.DATAFRAME
        elif payload.action == PayloadAction.AGENT_REPLY_PLOTLY.value:
            content = plotly.io.from_json(payload.message)
            t = MessageType.PLOTLY
        elif payload.action == PayloadAction.AGENT_REPLY_LOCATION.value:
            content = {
                'latitude': [payload.message['latitude']],
                'longitude': [payload.message['longitude']]
            }
            t = MessageType.LOCATION
        elif payload.action == PayloadAction.AGENT_REPLY_OPTIONS.value:
            t = MessageType.OPTIONS
            d = json.loads(payload.message)
            content = []
            for button in d.values():
                content.append(button)
        elif payload.action == PayloadAction.AGENT_REPLY_RAG.value:
            t = MessageType.RAG_ANSWER
            content = payload.message
        if content is not None:
            message = Message(t=t, content=content, is_user=False, timestamp=datetime.now())
            streamlit_session._session_state[agent_name][QUEUE].put(message)

        streamlit_session._handle_rerun_script_request()

    return on_message_with_agent_name


def on_error(ws, error):
    pass


def on_open(ws):
    pass


def on_close(ws, close_status_code, close_msg):
    pass


def on_ping(ws, data):
    pass


def on_pong(ws, data):
    pass