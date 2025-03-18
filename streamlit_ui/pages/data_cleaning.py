import json
import sys
from datetime import datetime

import streamlit as st
from besser.agent.core.message import Message, MessageType
from besser.agent.platforms.payload import PayloadAction, Payload, PayloadEncoder
from dateutil.relativedelta import relativedelta
from elasticsearch import Elasticsearch

from streamlit_ui.chat import load_chat
from streamlit_ui.initialization import initialize
from streamlit_ui.message_input import message_input
from streamlit_ui.pages.request import Request, Instruction, SemanticInstruction, FilterInstruction
from streamlit_ui.vars import ELASTICSEARCH, INSTRUCTIONS, INSTRUCTIONS_CHECKBOXES, WEBSOCKET, USER, QUEUE, HISTORY, PROGRESS

es_host = "localhost"
es_port = "19200"
index_name = "castor-test-enron"

action_dict = {
    'DOCUMENT_RELEVANCE': 'Document Relevance',
    'DOCUMENT_LABELS': 'Document Labels'
}

document_relevance_dict = {
    2: '🔫 Smoking gun',
    1: '👍 Relevant',
    -1: '👎 Not relevant'
}


def initialize_elasticsearch():
    if ELASTICSEARCH not in st.session_state:
        es_url = f'http://{es_host}:{es_port}'
        es = Elasticsearch([es_url])
        st.session_state[ELASTICSEARCH] = es

    if INSTRUCTIONS not in st.session_state:
        st.session_state[INSTRUCTIONS] = []
    if INSTRUCTIONS_CHECKBOXES not in st.session_state:
        st.session_state[INSTRUCTIONS_CHECKBOXES] = []

def semantic_instructions():
    def add_semantic_instruction():
        if st.session_state['instruction_input'] in [instruction.text for instruction in st.session_state[INSTRUCTIONS] if isinstance(instruction, SemanticInstruction)]:
            st.error('Instruction already exists')
            return
        semantic_instruction = SemanticInstruction(field=st.session_state['instruction_field'], text=st.session_state['instruction_input'])
        if semantic_instruction.text:
            st.session_state[INSTRUCTIONS].append(semantic_instruction)
            st.session_state[INSTRUCTIONS_CHECKBOXES].append(False)
        st.session_state['instruction_input'] = ""

    st.subheader('Semantic Instructions')
    cols = st.columns([0.2, 0.8])
    cols[0].selectbox(key='instruction_field', label='Select field', options=['SUBJECT', 'CONTENT', 'FROM', 'TO'], index=None)
    cols[1].text_input('Add semantic instruction:', key='instruction_input', on_change=add_semantic_instruction)


def filters():
    st.subheader('Filters')
    filter_cols = st.columns(3)
    filter_field = filter_cols[0].selectbox(key='filter_field', label='Select field',
                                            options=['SUBJECT', 'CONTENT', 'FROM', 'TO'], index=None)
    filter_operator = filter_cols[1].selectbox(key='filter_operator', label='Select operator', options=['equals', 'different', 'contains', 'starts with', 'regexp', 'fuzzy'],
                                               index=None)
    filter_value = filter_cols[2].text_input(key='filter_value', label='Enter value')
    if st.button('Add filter', disabled=not all([filter_field, filter_operator, filter_value])):
        filter_instruction = FilterInstruction(field=filter_field, operator=filter_operator, value=filter_value)
        if (filter_instruction.field, filter_instruction.operator, filter_instruction.value) in [
            (instruction.field, instruction.operator, instruction.value) for instruction in
            st.session_state[INSTRUCTIONS] if isinstance(instruction, FilterInstruction)]:
            st.error('Instruction already exists')
        else:
            st.session_state[INSTRUCTIONS].append(filter_instruction)
            st.session_state[INSTRUCTIONS_CHECKBOXES].append(False)


def instruction_checkboxes():
    instructions = st.session_state[INSTRUCTIONS]
    instructions_checkboxes = st.session_state[INSTRUCTIONS_CHECKBOXES]
    if len(instructions) > 0:
        st.subheader('**Applied filters and instructions**')
        for i, instruction in enumerate(instructions):
            instructions_checkboxes[i] = st.checkbox(key=f'checkbox_{instruction.to_str()}', label=instruction.to_str())
        if instructions_checkboxes:
            if st.button('Remove selection', disabled=not any(instructions_checkboxes), type='primary'):
                instructions = [i for i, b in zip(instructions, instructions_checkboxes) if not b]
                instructions_checkboxes = [b for b in instructions_checkboxes if
                                           not b]  # Only needed if you still need the filtered booleans list
                st.session_state[INSTRUCTIONS] = instructions
                st.session_state[INSTRUCTIONS_CHECKBOXES] = instructions_checkboxes
                st.rerun()

def create_request():
    request: Request = Request()
    with st.container(border=True):
        # Action and target value
        request.action = st.pills('Select action', ['DOCUMENT_RELEVANCE', 'DOCUMENT_LABELS'], format_func=(lambda x: action_dict[x]))
        if request.action == 'DOCUMENT_RELEVANCE':
            request.target_value = st.pills('Select value', options=[-1, 1, 2], format_func=(lambda x: document_relevance_dict[x]))
        elif request.action == 'DOCUMENT_LABELS':
            request.target_value = st.text_input('Enter label')
    with st.container(border=True):
        # Dates
        date_cols = st.columns(2)
        date_from = date_cols[0].date_input('Select Date Created (From)', value=None, min_value=datetime.today() - relativedelta(years=200), max_value=datetime.today() + relativedelta(years=200))
        if date_from:
            request.date_from = date_from.strftime('%Y-%m-%d')
        date_to = date_cols[1].date_input('Select Date Created (To)', value=None, min_value=datetime.today() - relativedelta(years=200), max_value=datetime.today() + relativedelta(years=200))
        if date_to:
            request.date_to = date_to.strftime('%Y-%m-%d')

        # Instructions
        filters()
        semantic_instructions()
        instruction_checkboxes()
        request.set_instructions(st.session_state[INSTRUCTIONS])
    return request


def submit_request(request):
    cols = st.columns(2)
    with cols[0].expander('Submit request', expanded=True):
        ready = True
        if not request.action:
            st.error('You need to select an action')
            ready = False
        if not request.target_value:
            st.error('You need to select a value for the action')
            ready = False
        if not (request.date_from or request.date_to or request.filters or request.semantic_instructions):
            st.error('''
                Please, set one of the following to submit your request:
                1. Date From
                2. Date To
                3. Add a filter
                4. Add a semantic instruction
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
        st.json(request.to_json(), expanded=True)
    with cols[1].expander('Agent', expanded=True):
        load_chat()


def data_cleaning():
    initialize_elasticsearch()
    # es: Elasticsearch = st.session_state[ELASTICSEARCH]
    # mapping = es.indices.get_mapping(index=index_name).body
    # st.write(mapping)
    request = create_request()
    submit_request(request)


