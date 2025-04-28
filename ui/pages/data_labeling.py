import json
from datetime import datetime

import streamlit as st
from besser.agent.core.message import Message, MessageType
from besser.agent.platforms.payload import PayloadAction, Payload, PayloadEncoder
from dateutil.relativedelta import relativedelta
from elasticsearch import Elasticsearch

from ui.agent.chat import load_chat, load_progress_bar
from query.request import Request, Instruction, Filter
from ui.agent.message_input import message_input
from ui.utils import get_page_height
from ui.vars import *


def initialize_elasticsearch(es_host, es_port):
    if ELASTICSEARCH not in st.session_state:
        es_url = f'http://{es_host}:{es_port}'
        es = Elasticsearch([es_url])
        st.session_state[ELASTICSEARCH] = es


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
    cols = st.columns([0.2, 0.8])
    cols[0].selectbox(key=INSTRUCTION_FIELD, label='Select field', options=[SUBJECT, CONTENT, FROM, TO], index=None)
    cols[1].text_input('Add instruction:', key=INSTRUCTION_INPUT, on_change=add_instruction)
    checkboxes(INSTRUCTIONS, INSTRUCTIONS_CHECKBOXES)


def filters():
    st.subheader('Filters')
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
    action_tab, date_tab, filters_tab, instructions_tab, submit_tab = st.tabs(['Action', 'Date', 'Filters', 'Instructions', 'Submit'])
    with action_tab:
        # Action and target value
        request.action = st.pills('Select action', [DOCUMENT_RELEVANCE, DOCUMENT_LABELS], format_func=(lambda x: action_dict[x]))
        if request.action == DOCUMENT_RELEVANCE:
            request.target_value = st.pills('Select value', options=document_relevance_dict.keys(), format_func=(lambda x: document_relevance_dict[x]))
        elif request.action == DOCUMENT_LABELS:
            request.target_value = st.text_input('Enter label')
    with date_tab:
        # Dates
        date_cols = st.columns(2)
        date_from = date_cols[0].date_input('Select Date Created (From)', value=None, min_value=datetime.today() - relativedelta(years=200), max_value=datetime.today() + relativedelta(years=200))
        if date_from:
            request.date_from = date_from.strftime(DATE_FORMAT)
        date_to = date_cols[1].date_input('Select Date Created (To)', value=None, min_value=datetime.today() - relativedelta(years=200), max_value=datetime.today() + relativedelta(years=200))
        if date_to:
            request.date_to = date_to.strftime(DATE_FORMAT)
    with filters_tab:
        filters()
    with instructions_tab:
        instructions()
    request.filters = st.session_state[FILTERS]
    request.instructions = st.session_state[INSTRUCTIONS]
    with submit_tab:
        submit_request(request)
    return request


def submit_request(request):
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
        st.session_state[HISTORY].clear()
        if PROGRESS in st.session_state:
            del st.session_state[PROGRESS]
        message = 'Request submitted'  # TODO: Add request reference number, store ref content, user and (later) the answer
        message = Message(t=MessageType.STR, content=message, is_user=True, timestamp=datetime.now())
        st.session_state[HISTORY].append(message)
        payload = Payload(action=PayloadAction.USER_MESSAGE,
                          message=json.dumps(request.to_json()))
        try:
            ws = st.session_state[WEBSOCKET]
            ws.send(json.dumps(payload, cls=PayloadEncoder))
            st.rerun()
        except Exception as e:
            st.error('Your message could not be sent. The connection is already closed')
    st.text('Check the content of the request:')
    st.json(request.to_json(), expanded=False)


def data_labeling():
    st.header('Data Labeling')
    cols = st.columns(2)
    with cols[0].container(height=get_page_height(subtract=150)):
        create_request()
    with cols[1]:
        with st.container(height=get_page_height(subtract=422)):
            load_chat()
        message_input()
        with st.container(border=True, height=200):
            load_progress_bar()


