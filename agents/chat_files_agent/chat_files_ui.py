import json
import os
from datetime import datetime
from io import StringIO

import streamlit as st
import streamlit_antd_components as sac
from besser.agent.core.file import File
from besser.agent.platforms.payload import Payload, PayloadAction, PayloadEncoder
from streamlit.components.v1 import html
from streamlit.runtime.uploaded_file_manager import UploadedFile

from agents.chat_files_agent.chat_data import User, Chat, Message
from agents.chat_files_agent.json_loader import json_loader
from agents.chat_files_agent.utils import generate_light_color, blankspace_to_underscore, html_text_processing
from agents.chat_files_agent.whatsapp_loader import whatsapp_loader
from agents.utils.chat import load_chat
from agents.utils.message_input import message_input
from app.vars import *


def process_attachments(attachments: list[UploadedFile]) -> list[File]:
    files: list[File] = []
    for attachment in attachments:
        file: File = File(file_name=attachment.name, file_type=attachment.type, file_data=attachment.getvalue())
        files.append(file)
    return files


def import_chat():
    chat = None
    st.subheader('Import a new chat file')
    chat_type: str = st.selectbox(label="What kind of chat are you importing?", options=CHAT_TYPES, index=0)
    chat_name = st.text_input(label='Name of the chat')
    new_chat_file = st.file_uploader("Upload a new chat file", accept_multiple_files=False)
    if new_chat_file:
        stringio = StringIO(new_chat_file.getvalue().decode("utf-8"))
        string_data = stringio.read()
        if chat_type == WHATSAPP:
            chat = whatsapp_loader(name=chat_name, whatsapp_chat=string_data)
    ok = chat and chat_name
    if st.button(label='Load', disabled=not ok, type='primary'):
        folder_path = st.secrets[CHATS_DIRECTORY]
        file_path = os.path.join(folder_path, f'{chat_name}.json')
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(chat.to_json(), f, indent=2)
        st.success('Your chat has been imported successfully')


def select_chat() -> (Chat, list[File]):
    chat, attachments = None, None
    chat_files = os.listdir(st.secrets[CHATS_DIRECTORY])
    if not chat_files:
        st.info('There are no existing chats. Go to the Import tab to create a new one.')
        return None, None
    chat_file_name = st.radio(label='Select a chat', options=chat_files, index=None)
    if chat_file_name:
        file_path = str(os.path.join(st.secrets[CHATS_DIRECTORY], chat_file_name))
        chat = json_loader(file_path)
        if chat.name != st.session_state[AGENT_CHAT_FILES][CHAT_NAME]:
            # Send the name of the selected chat file to the agent
            st.session_state[AGENT_CHAT_FILES][CHAT_NAME] = chat.name
            payload = Payload(action=PayloadAction.USER_MESSAGE,
                              message=json.dumps({CHAT: chat_file_name}))
            try:
                ws = st.session_state[AGENT_CHAT_FILES][WEBSOCKET]
                ws.send(json.dumps(payload, cls=PayloadEncoder))
            except Exception as e:
                st.error('Your message could not be sent. The connection is already closed')
    else:
        st.session_state[AGENT_CHAT_FILES][CHAT_NAME] = None
    attachments_files: list[UploadedFile] = st.file_uploader("Upload attachments", accept_multiple_files=True)
    if attachments_files:
        attachments: list[File] = process_attachments(attachments_files)
    else:
        attachments = []
    return chat, attachments


def config_chat(chat: Chat):
    # TODO: ADD BUTTON TO UPDATE JSON FILE
    chat.config.view_attachments = st.toggle(label="View attachments", value=False)
    chat.config.right_aligned = st.toggle(label="Right-aligned messages", value=False)
    chat.config.show_timestamps = st.toggle(label="Show timestamps", value=True)
    chat.config.page_size = st.number_input("Page size", value=100, min_value=1)
    chat.config.container_height = st.slider(label="Chat container height (px)", min_value=200, max_value=2000, value=650)
    chat.owner = st.selectbox(label="Who is the user?", options=chat.users, index=None, format_func=lambda u: u.name)
    chat.config.selected_message = st.number_input(label='[Test feature] Go to message', value=None, min_value=1, max_value=chat.num_messages())
    chat.config.selected_date = st.date_input(label='[Test feature] Go to date', value=None)
    # todo: show/hide hidden messages
    # todo: unhide all messages


def notebook(chat: Chat):
    col1, col2 = st.columns(2)
    col1.subheader('Notebook')
    if 'message_ids' in st.session_state:
        for message_id in st.session_state['message_ids']:
            if st.button(f'Message {message_id}', key=f'message_id_{message_id}'):
                chat.config.selected_message = message_id

    with open(st.secrets[CHAT_NOTEBOOK_FILE], "r", encoding='utf-8') as file:
        file_name = os.path.basename(st.secrets[CHAT_NOTEBOOK_FILE])
        col2.download_button(
            label=f"Download {file_name}",
            data=file,
            file_name=file_name,
            icon=":material/download:",
            mime="application/json"
        )
    with open(st.secrets[CHAT_NOTEBOOK_FILE], "r", encoding='utf-8') as file:
        notebook = json.load(file)
    # TODO: Currently, only topic entries
    notebook_conteiner = col1.container(height=400, border=True)
    messages_conteiner = col2.container(height=400, border=True)
    topic_entries = [entry for entry in notebook if (entry[ENTRY_TYPE] == 'topic' and entry[CHAT_NAME] == st.session_state[AGENT_CHAT_FILES][CHAT_NAME])]
    selected_topic_entry = notebook_conteiner.radio(label=f'Select a topic', options=topic_entries, format_func=lambda entry: entry[TOPIC])
    if selected_topic_entry:
        messages_conteiner.text(f'Messages about "{selected_topic_entry[TOPIC]}"')
        messages_conteiner.text(f'Created at: "{selected_topic_entry[TIMESTAMP]}"')
        for message_id in selected_topic_entry[MESSAGE_IDS]:
            if messages_conteiner.button(label=f'Message {message_id}', key=f'message_button_{message_id}'):
                chat.config.selected_message = message_id


def chat_files():
    cols = st.columns(2)
    with cols[0]:
        st.header('Chat Files')
        chat_list_tab, import_tab, config_tab, agent_tab, notebook_tab = st.tabs(['📋 Chats', '🗂️ Import', '🛠️ Configuration', '🤖 Agent', '📖 Notebook'])

    with import_tab:
        import_chat()

    with chat_list_tab:
        chat, attachments = select_chat()

    with config_tab:
        if chat:
            config_chat(chat)

    with notebook_tab:
        notebook(chat)

    with cols[1]:
        if chat:
            display_chat(chat, attachments=attachments)
            add_js_for_scrolling(chat)

    with agent_tab:
        chat_container = st.container(height=520)
        message_input(AGENT_CHAT_FILES)
        with chat_container:
            load_chat(AGENT_CHAT_FILES)


def display_chat(chat: Chat, attachments: list[File] = None):
    chat_container = st.container(height=chat.config.container_height)
    if chat.config.selected_date or chat.config.selected_message:
        chat.config.selected_page = int(sac.pagination(index=chat.config.selected_page, align='center', jump=True, show_total=True, page_size=chat.config.page_size, total=chat.num_messages()))
        st.session_state[AGENT_CHAT_FILES][CHAT_PAGE] = chat.config.selected_page
    else:
        chat.config.selected_page = int(sac.pagination(index=st.session_state[AGENT_CHAT_FILES][CHAT_PAGE], align='center', jump=True, show_total=True, page_size=chat.config.page_size, total=chat.num_messages()))
    colors = {}
    for user in chat.users:
        colors[user.name] = generate_light_color(user.name)
        messages_css = f"""
            <style>
                .user_{blankspace_to_underscore(user.name)} {{
                    background-color: {colors[user.name]};
                    max-width: {'80%' if chat.config.right_aligned else '100%'};
                    font-size: 16px;
                    margin-left: {'auto' if (user==chat.owner and chat.config.right_aligned) else '0'};
                    width: {'fit-content' if chat.config.right_aligned else 'auto'};
                    text-align: {'right' if (user==chat.owner and chat.config.right_aligned) else 'left'};
                    padding: 10px 10px 1px 10px;
                    border-radius: 10px;
                    margin-bottom: 10px;
                    box-shadow: 0 1px 8px rgba(0, 0, 0, 0.2);
                }}
                .message_timestamp {{
                    font-size: 12px;
                    padding: -10px 0px 0px 0px;
                }}
            </style>
            """
        st.markdown(messages_css, unsafe_allow_html=True)
    last_user: User | None = None
    last_datetime: datetime | None = None
    with chat_container:
        for message in chat.get_messages():
            print_message(message, last_datetime, last_user, chat.owner, chat.config, get_attachment(message, attachments))
            last_datetime = message.timestamp
            last_user = message.user


def get_attachment(message: Message, attachments: list[File]) -> File:
    for attachment in attachments:
        if attachment.name == message.extract_attachment_name():
            return attachment
    return None


def print_message(message: Message, last_datetime, last_user, owner, config, attachment: File or None):
    # Add date divider
    if not last_datetime or message.timestamp.date() != last_datetime.date():
        st.markdown(
            f"""<div id="date_divider_{message.timestamp.strftime("%d_%B_%Y")}" style="text-align: center; margin-bottom: 5px; border-radius: 10px; {'border: 3px solid #ff0026;' if message.timestamp.date() == config.get_selected_date_or_next() else ''}">{message.timestamp.strftime("%d %B %Y")}</div><hr style="margin-top: 0px;">""",
            unsafe_allow_html=True)
    # Write username when changing user
    if message.user != last_user:
        align = 'right' if (message.user == owner and config.right_aligned) else 'left'
        st.markdown(f'<div style="text-align: {align};">{message.user.name}</div>', unsafe_allow_html=True)
    if attachment and config.view_attachments:
        # TODO: SUPPORT ALL ATTACHMENT TYPES
        if attachment.type.startswith('image'):
            message_markdown = f"""
                        <div id="message_{message.id}" class="user_{blankspace_to_underscore(message.user.name)}" style="{'border: 3px solid #ff0026;' if message.id == config.selected_message else ''}">
                            <img src="data:image/png;base64,{attachment.base64}" style="width: 300px; margin-bottom: 10px;" alt="Image" />
                            {f'<p class="message_timestamp" style="margin-top: 0px;">{message.timestamp}</p>' if config.show_timestamps else ''}
                        </div>
                        """
        elif attachment.type.startswith('video'):
            message_markdown = f"""
                        <div id="message_{message.id}" class="user_{blankspace_to_underscore(message.user.name)}" style="{'border: 3px solid #ff0026;' if message.id == config.selected_message else ''}">
                            <video controls width="300px">
                                <source src="data:video/mp4;base64,{attachment.base64}" type="video/mp4">
                                Your browser does not support the video tag.
                            </video>
                            {f'<p class="message_timestamp" style="margin-top: 0px;">{message.timestamp}</p>' if config.show_timestamps else ''}
                        </div>
                        """
        elif attachment.type.startswith('audio'):
            message_markdown = f"""
                        <div id="message_{message.id}" class="user_{blankspace_to_underscore(message.user.name)}" style="{'border: 3px solid #ff0026;' if message.id == config.selected_message else ''}">
                            <audio controls style="width: 500px;">
                                <source src="data:audio/mp4;base64,{attachment.base64}" type="audio/mp4">
                                Your browser does not support the audio tag.
                            </audio>
                            {f'<p class="message_timestamp" style="margin-top: 0px;">{message.timestamp}</p>' if config.show_timestamps else ''}
                        </div>
                        """
        else:
            message_markdown = f"""
                        <div id="message_{message.id}" class="user_{blankspace_to_underscore(message.user.name)}" style="{'border: 3px solid #ff0026;' if message.id == config.selected_message else ''}">
                            <p text-align: left;">
                                {html_text_processing(message.content)}
                                <br>
                                ATTACHMENT TYPE NOT SUPPORTED
                            </p>
                            {f'<p class="message_timestamp" style="margin-top: 0px;">{message.timestamp}</p>' if config.show_timestamps else ''}
                        </div>
                        """
    else:
        message_markdown = f"""
                    <div id="message_{message.id}" class="user_{blankspace_to_underscore(message.user.name)}" style="{'border: 3px solid #ff0026;' if message.id == config.selected_message else ''}">
                        <p style="{'margin-bottom: 1px;' if config.show_timestamps else ""} text-align: left;">
                            {html_text_processing(message.content)}
                        </p>
                        {f'<p class="message_timestamp" style="margin-top: 0px;">{message.timestamp}</p>' if config.show_timestamps else ''}
                    </div>
                    """
    st.markdown(message_markdown, unsafe_allow_html=True)


def add_js_for_scrolling(chat: Chat):
    element_id = None
    if chat.config.selected_message:
        element_id = f"message_{chat.config.selected_message}"
    if chat.config.selected_date:
        # TODO: This replaces selected message if both are set
        date = chat.config.get_selected_date_or_next()
        if date:
            element_id = f"date_divider_{date.strftime('%d_%B_%Y')}"
    if element_id:
        js = f"""
                <script>
                    function scrollToMessage() {{
                        const target = parent.document.getElementById("{element_id}");
                        target.scrollIntoView({{
                            behavior: 'smooth',
                            block: 'center' // Try 'start', 'center', 'end', or 'nearest'
                        }});
                    }}
                scrollToMessage()
                </script>
            """
        with st.container(height=1, border=False):
            html(js)
