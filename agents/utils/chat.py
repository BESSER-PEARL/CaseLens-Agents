import base64
import json
import time
from datetime import datetime

import streamlit as st

from besser.agent.core.file import File
from besser.agent.core.message import Message, MessageType
from besser.agent.platforms.payload import Payload, PayloadAction, PayloadEncoder

from app.vars import *

user_type = {
    0: ASSISTANT,
    1: USER
}


def stream_text(text: str):
    def stream_callback():
        for word in text.split(" "):
            yield word + " "
            time.sleep(TYPING_TIME)
    return stream_callback


def write_or_stream(content, stream: bool):
    if stream:
        st.write_stream(stream_text(content))
    else:
        st.write(content)


def write_message(agent_name: str, message: Message, key_count: int, stream: bool = False):
    key = f'message_{key_count}'
    with st.chat_message(user_type[message.is_user]):
        if message.type == MessageType.AUDIO:
            st.audio(message.content, format="audio/wav")

        elif message.type == MessageType.FILE:
            file: File = File.from_dict(message.content)
            file_name = file.name
            file_type = file.type
            file_data = base64.b64decode(file.base64.encode('utf-8'))
            st.download_button(label='Download ' + file_name, file_name=file_name, data=file_data, mime=file_type, key=key)

        elif message.type == MessageType.IMAGE:
            st.image(message.content)

        elif message.type == MessageType.OPTIONS:
            def send_option():
                option = st.session_state[key]
                message = Message(t=MessageType.STR, content=option, is_user=True, timestamp=datetime.now())
                st.session_state[agent_name][HISTORY].append(message)
                payload = Payload(action=PayloadAction.USER_MESSAGE, message=option)
                ws = st.session_state[agent_name][WEBSOCKET]
                ws.send(json.dumps(payload, cls=PayloadEncoder))
                st.session_state[key] = None

            st.pills(label='Choose an option', options=message.content, selection_mode='single', on_change=send_option, key=key)

        elif message.type == MessageType.LOCATION:
            st.map(message.content)

        elif message.type == MessageType.HTML:
            st.html(message.content)

        elif message.type == MessageType.DATAFRAME:
            st.dataframe(message.content, key=key)

        elif message.type == MessageType.PLOTLY:
            st.plotly_chart(message.content, key=key)

        elif message.type == MessageType.RAG_ANSWER:
            # TODO: Add stream text
            write_or_stream(f'🔮 {message.content["answer"]}', stream)
            with st.expander('Details'):
                write_or_stream(f'This answer has been generated by an LLM: **{message.content["llm_name"]}**', stream)
                write_or_stream(f'It received the following documents as input to come up with a relevant answer:', stream)
                if 'docs' in message.content:
                    for i, doc in enumerate(message.content['docs']):
                        st.write(f'**Document {i + 1}/{len(message.content["docs"])}**')
                        st.write(f'- **Source:** {doc["metadata"]["source"]}')
                        st.write(f'- **Page:** {doc["metadata"]["page"]}')
                        st.write(f'- **Content:** {doc["content"]}')

        elif message.type in [MessageType.STR, MessageType.MARKDOWN]:
            write_or_stream(message.content, stream)


def load_chat(agent_name: str):
    key_count = 0
    for message in st.session_state[agent_name][HISTORY]:
        write_message(agent_name, message, key_count, stream=False)
        key_count += 1

    while not st.session_state[agent_name][QUEUE].empty():
        message = st.session_state[agent_name][QUEUE].get()
        st.session_state[agent_name][HISTORY].append(message)
        write_message(agent_name, message, key_count, stream=True)
        key_count += 1
