from datetime import datetime

import streamlit as st

from agents.utils.json_utils import update_json_file
from app.vars import *


def add_notebook_find_topic_entry(chat_name: str, topic: str, message_ids: list[int]):
    entry = {
        ENTRY_TYPE: FIND_TOPIC,
        CHAT_NAME: chat_name,
        TIMESTAMP: datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        TOPIC: topic,
        MESSAGE_IDS: message_ids
    }
    update_json_file(filepath=st.secrets[CHAT_NOTEBOOK_FILE], new_entries=[entry])


def add_notebook_hide_topic_entry(chat_name: str, topic: str, message_ids: list[int]):
    entry = {
        ENTRY_TYPE: HIDE_TOPIC,
        ENABLED: True,
        CHAT_NAME: chat_name,
        TIMESTAMP: datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        TOPIC: topic,
        MESSAGE_IDS: message_ids
    }
    update_json_file(filepath=st.secrets[CHAT_NOTEBOOK_FILE], new_entries=[entry])
