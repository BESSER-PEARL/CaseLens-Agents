import re
import streamlit as st
from datetime import datetime

from agents.chat_files_agent.chat_data import User, Chat, WhatsAppMessage
from app.vars import WHATSAPP


@st.cache_resource(max_entries=1)
def whatsapp_loader(whatsapp_chat: str):
    chat: Chat = Chat(chat_type=WHATSAPP)
    pattern = r'^\[(\d{2}/\d{2}/\d{4}), (\d{2}:\d{2}:\d{2})\] ([^:]+): (.+)$'
    attachment_pattern = r'^\[(\d{2}/\d{2}/\d{4}), (\d{2}:\d{2}:\d{2})\] ([^:]+):\s*<attached: (.+?)>$'

    last_message: WhatsAppMessage | None = None
    pending_lines: list[str] = []
    i = 1
    for line in whatsapp_chat.splitlines():
        line = line.replace('\u200e', '').replace('\u200f', '').strip()
        match = re.match(pattern, line)
        attachment_match = re.match(attachment_pattern, line)
        if match:
            # Attach any pending lines to the previous message
            if last_message and pending_lines:
                last_message.content += '\n' + '\n'.join(pending_lines)
                pending_lines = []

            date, time, username, content = match.groups()
            timestamp_str = f"{date} {time}"
            timestamp = datetime.strptime(timestamp_str, "%d/%m/%Y %H:%M:%S")
            message: WhatsAppMessage = WhatsAppMessage(id=i, user=User(name=username), timestamp=timestamp, content=content)
            i += 1
            chat.add_message(message)
            last_message = message
        elif attachment_match:
            # Attach any pending lines to the previous message
            if last_message and pending_lines:
                last_message.content += '\n' + '\n'.join(pending_lines)
                pending_lines = []
            date, time, username, attachment = match.groups()
            timestamp_str = f"{date} {time}"
            timestamp = datetime.strptime(timestamp_str, "%d/%m/%Y %H:%M:%S")
            message: WhatsAppMessage = WhatsAppMessage(id=i, user=User(name=username), timestamp=timestamp, content=attachment)
            i += 1
            chat.add_message(message)
            last_message = message
        else:
            # Line is a continuation of the previous message
            if last_message:
                pending_lines.append(line)
            else:
                print("Line outside message context:", line)

    # In case the last message had pending lines at the end of the file
    if last_message and pending_lines:
        last_message.content += '\n' + '\n'.join(pending_lines)
    return chat