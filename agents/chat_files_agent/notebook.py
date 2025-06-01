from datetime import datetime

import streamlit as st

from agents.utils.json_utils import update_json_file
from app.vars import *


def add_notebook_topic_entry(chat_name: str, topic: str, message_ids: list[int]):
    entry = {
        ENTRY_TYPE: 'topic',
        CHAT_NAME: chat_name,
        TIMESTAMP: datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        TOPIC: topic,
        MESSAGE_IDS: message_ids
    }
    update_json_file(filepath=st.secrets[CHAT_NOTEBOOK_FILE], new_entries=[entry])
