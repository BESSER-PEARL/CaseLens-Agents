import json
import os
from datetime import datetime

import streamlit as st
from besser.agent.core.message import Message, MessageType
from besser.agent.platforms.payload import PayloadAction, Payload, PayloadEncoder
from dateutil.relativedelta import relativedelta
from elasticsearch import Elasticsearch

from agents.data_labeling_agent.request_history import update_json_file, iterate_json_file
from agents.utils.chat import load_chat, load_progress_bar
from agents.data_labeling_agent.request import Request, Instruction, Filter
from agents.utils.message_input import message_input
from app.vars import *


def action(request: Request):
    # Action and target value
    st.subheader('Action')
    st.text('🎯 Select the action you want to perform on the database documents')
    request.action = st.pills('Select action', [DOCUMENT_RELEVANCE, DOCUMENT_LABELS],
                              format_func=(lambda x: action_dict[x]))
    if request.action == DOCUMENT_RELEVANCE:
        request.target_value = st.pills('Select value', options=document_relevance_dict.keys(),
                                        format_func=(lambda x: document_relevance_dict[x]))
    elif request.action == DOCUMENT_LABELS:
        request.target_value = st.text_input('Enter label')


def date(request: Request):
    # Dates
    st.subheader('Date')
    st.text('🗓️ You can filter the documents by date (from and/or to)')
    date_cols = st.columns(2)
    date_from = date_cols[0].date_input('Date Created (From)', value=None,
                                        min_value=datetime.today() - relativedelta(years=200),
                                        max_value=datetime.today() + relativedelta(years=200))
    if date_from:
        request.date_from = date_from.strftime(DATE_FORMAT)
    date_to = date_cols[1].date_input('Date Created (To)', value=None,
                                      min_value=datetime.today() - relativedelta(years=200),
                                      max_value=datetime.today() + relativedelta(years=200))
    if date_to:
        request.date_to = date_to.strftime(DATE_FORMAT)


def instructions():
    def add_instruction():
        if st.session_state[INSTRUCTION_INPUT] in [instruction.text for instruction in st.session_state[INSTRUCTIONS]]:
            st.error('Instruction already exists')
            return
        instruction = Instruction(field=st.session_state[INSTRUCTION_FIELD], text=st.session_state[INSTRUCTION_INPUT])
        if instruction.text:
            st.session_state[INSTRUCTIONS].append(instruction)
            st.session_state[INSTRUCTIONS_CHECKBOXES].append(False)
        st.session_state[INSTRUCTION_INPUT] = ""

    st.subheader('Instructions')
    st.text('✍️ Define your own filters using natural language.')
    st.text('You can assign instructions to a specific document field or all fields (leaving it empty)')
    st.selectbox(key=INSTRUCTION_FIELD, label='Select field', options=[SUBJECT, CONTENT, FROM, TO], index=None, placeholder='Choose a field or leave empty')
    st.text_input('Add instruction:', key=INSTRUCTION_INPUT, on_change=add_instruction, placeholder='Example: An email where 2 companies are agreeing on prices')
    checkboxes(INSTRUCTIONS, INSTRUCTIONS_CHECKBOXES)


def filters():
    st.subheader('Filters')
    st.text('🔍 You can apply filters to your request.')
    st.text('Select a document field, an operator and a value.')
    st.text("Example: SUBJECT contains price")
    with st.expander('Check the operators documentation', expanded=False):
        st.markdown('- **equals**: Matches documents where the field value is exactly equal to the specified value.')
        st.markdown('- **different**: Matches documents where the field value is not equal to the specified value.')
        st.markdown('- **contains**: Matches documents where the field contains the specified substring (case-sensitive).')
        st.markdown('- **starts** with: Matches documents where the field value starts with the specified prefix.')
        st.markdown('- **regexp**: Matches documents where the field value satisfies the given regular expression.')
        st.markdown('- **fuzzy**: Matches documents where the field value is similar to the specified term, allowing for spelling errors.')

    filter_cols = st.columns(4)
    filter_field = filter_cols[0].selectbox(
        key=FILTER_FIELD,
        placeholder='Field',
        label='Select field',
        label_visibility='collapsed',
        options=[SUBJECT, CONTENT, FROM, TO],
        index=None
    )
    filter_operator = filter_cols[1].selectbox(
        key=FILTER_OPERATOR,
        placeholder='Operator',
        label='Select operator',
        label_visibility='collapsed',
        options=[EQUALS, DIFFERENT, CONTAINS, STARTS_WITH, REGEXP, FUZZY],
        index=None
    )
    filter_value = filter_cols[2].text_input(
        key=FILTER_VALUE,
        placeholder='Value',
        label='Enter value',
        label_visibility='collapsed'
    )
    if filter_cols[3].button('Add filter', disabled=not all([filter_field, filter_operator, filter_value])):
        filter = Filter(field=filter_field, operator=filter_operator, value=filter_value)
        if (filter.field, filter.operator, filter.value) in [(filter.field, filter.operator, filter.value) for filter in st.session_state[FILTERS]]:
            st.error('Filter already exists')
        else:
            st.session_state[FILTERS].append(filter)
            st.session_state[FILTERS_CHECKBOXES].append(False)
    checkboxes(FILTERS, FILTERS_CHECKBOXES)


def checkboxes(key: str, checkboxes_key: str):
    instructions = st.session_state[key]
    instructions_checkboxes = st.session_state[checkboxes_key]
    if len(instructions) > 0:
        for i, instruction in enumerate(instructions):
            instructions_checkboxes[i] = st.checkbox(key=f'checkbox_{instruction.to_str()}', label=instruction.to_str())
        if instructions_checkboxes:
            if st.button('Remove selection', disabled=not any(instructions_checkboxes), type='primary', key=f'checkboxes_{key}'):
                instructions = [i for i, b in zip(instructions, instructions_checkboxes) if not b]
                instructions_checkboxes = [b for b in instructions_checkboxes if not b]  # Only needed if you still need the filtered booleans list
                st.session_state[key] = instructions
                st.session_state[checkboxes_key] = instructions_checkboxes
                st.rerun()


def create_request():
    request: Request = Request()
    action_tab, date_tab, filters_tab, instructions_tab, submit_tab, history_tab = st.tabs(['🎯 Action', '🗓️ Date', '🔍 Filters', '✍️ Instructions', '📨 Send Request', '📜 History'])
    with action_tab:
        action(request)
    with date_tab:
        date(request)
    with filters_tab:
        filters()
    with instructions_tab:
        instructions()
    request.filters = st.session_state[FILTERS]
    request.instructions = st.session_state[INSTRUCTIONS]
    with submit_tab:
        load_progress_bar()
        submit_request(request)
    with history_tab:
        load_progress_bar()
        request_history()
    return request


def request_history():
    st.subheader('History of requests')
    with open(st.secrets[REQUEST_HISTORY_FILE], "rb") as file:
        file_name = os.path.basename(st.secrets[REQUEST_HISTORY_FILE])
        st.download_button(
            label=f"Download {file_name}",
            data=file,
            file_name=file_name,
            icon=":material/download:",
            mime="application/json"
        )
    for i, r in enumerate(iterate_json_file(st.secrets[REQUEST_HISTORY_FILE])):
        with st.expander(f"Request #{i + 1} at {r[TIMESTAMP]}", expanded=False):
            if st.button('Submit', type='primary', use_container_width=True, key=f'submit_{i}'):
                request = Request(
                    action=r[ACTION],
                    target_value=r[TARGET_VALUE],
                    date_from=r[DATE_FROM],
                    date_to=r[DATE_TO],
                    filters=[Filter(field=f[FIELD], operator=f[OPERATOR], value=f[VALUE]) for f in r[FILTERS]],
                    instructions=[Instruction(field=f[FIELD], text=f[TEXT]) for f in r[INSTRUCTIONS]],
                    timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
                # st.session_state[HISTORY].clear()
                request_json = request.to_json()
                update_json_file(st.secrets[REQUEST_HISTORY_FILE], [request_json])
                if PROGRESS in st.session_state:
                    del st.session_state[PROGRESS]
                message = f'Request #{request.id} submitted'
                message = Message(t=MessageType.STR, content=message, is_user=True, timestamp=datetime.now())
                st.session_state[HISTORY].append(message)
                payload = Payload(action=PayloadAction.USER_MESSAGE,
                                  message=json.dumps(request_json))
                try:
                    ws = st.session_state[WEBSOCKET]
                    ws.send(json.dumps(payload, cls=PayloadEncoder))
                    st.rerun()
                except Exception as e:
                    st.error('Your message could not be sent. The connection is already closed')
            st.json(r)


def submit_request(request):
    st.text('📨 Once you have completed your request, send it to the agent.')
    ready = True
    if not request.action:
        st.error('You need to select an action')
        ready = False
    if not request.target_value:
        st.error('You need to select a value for the action')
        ready = False
    if not (request.date_from or request.date_to or request.filters or request.instructions):
        st.error('''
            Please, set one of the following to submit your request:
            1. Date From
            2. Date To
            3. Add a filter
            4. Add an instruction
            ''')
        ready = False
    if st.button('Submit', disabled=not ready, type='primary', use_container_width=True):
        # st.session_state[HISTORY].clear()
        request.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        request_json = request.to_json()
        update_json_file(st.secrets[REQUEST_HISTORY_FILE], [request_json])
        if PROGRESS in st.session_state:
            del st.session_state[PROGRESS]
        message = f'Request #{request.id} submitted'
        message = Message(t=MessageType.STR, content=message, is_user=True, timestamp=datetime.now())
        st.session_state[HISTORY].append(message)
        payload = Payload(action=PayloadAction.USER_MESSAGE,
                          message=json.dumps(request_json))
        try:
            ws = st.session_state[WEBSOCKET]
            ws.send(json.dumps(payload, cls=PayloadEncoder))
            st.rerun()
        except Exception as e:
            st.error('Your message could not be sent. The connection is already closed')
    st.text('Check the content of the request:')
    st.json(request.to_json(), expanded=False)


def data_labeling():
    cols = st.columns(2)
    with cols[0]:
        st.header('Data Labeling')
        create_request()
    with cols[1]:
        st.subheader('Agent')
        chat_container = st.container(height=500)
        message_input()
        with chat_container:
            load_chat()


