import json
from datetime import datetime

import streamlit as st

from besser.agent.core.message import Message, MessageType
from besser.agent.platforms.payload import Payload, PayloadAction, PayloadEncoder

from app.vars import SUBMIT_TEXT, USER, WEBSOCKET


def message_input():
    def submit_text():
        # Necessary callback due to buf after 1.27.0 (https://github.com/streamlit/streamlit/issues/7629)
        # It was fixed for rerun but with _handle_rerun_script_request it doesn't work
        st.session_state[SUBMIT_TEXT] = True

    user_input = st.chat_input("Chat here", on_submit=submit_text)
    if st.session_state[SUBMIT_TEXT]:
        st.session_state[SUBMIT_TEXT] = False
        message = Message(t=MessageType.STR, content=user_input, is_user=True, timestamp=datetime.now())
        st.session_state.history.append(message)
        payload = Payload(action=PayloadAction.USER_MESSAGE,
                          message=user_input)
        try:
            ws = st.session_state[WEBSOCKET]
            ws.send(json.dumps(payload, cls=PayloadEncoder))
        except Exception as e:
            st.error('Your message could not be sent. The connection is already closed')
