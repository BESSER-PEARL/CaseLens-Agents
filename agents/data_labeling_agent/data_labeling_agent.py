# You may need to add your working directory to the Python path. To do so, uncomment the following lines of code
# import sys
# sys.path.append("/Path/to/directory/agentic-framework") # Replace with your directory path
import json
import logging
import operator

from besser.agent.core.agent import Agent
from besser.agent.core.session import Session
from besser.agent.exceptions.logger import logger
from besser.agent.library.transition.events.base_events import ReceiveJSONEvent, ReceiveTextEvent
from besser.agent.nlp.intent_classifier.intent_classifier_configuration import LLMIntentClassifierConfiguration
from besser.agent.nlp.llm.llm_openai_api import LLMOpenAI
from elasticsearch import Elasticsearch

from agents.elasticsearch.elasticsearch_query import build_query, get_num_docs, update_document_relevance_query, \
    append_document_label_query, scroll_docs
from app.vars import *

# Configure the logging module (optional)
logger.setLevel(logging.INFO)

# Create the agent
data_labeling_agent = Agent('data_labeling_agent')
# Load agent properties stored in a dedicated file
data_labeling_agent.load_properties('agents/config.ini')
# Define the platform your agent will use
websocket_platform = data_labeling_agent.use_websocket_platform(use_ui=False)


# Create the LLM
llm = LLMOpenAI(
    agent=data_labeling_agent,
    name='gpt-4o-mini',
    parameters={
        # 'max_completion_tokens': 1,
        # 'response_format': {"type": "json_object"}
    }
)

llm_ic_config = LLMIntentClassifierConfiguration(
    llm_name='gpt-4o-mini',
    parameters={},
    use_intent_descriptions=True,
    use_training_sentences=False,
    use_entity_descriptions=True,
    use_entity_synonyms=False
)

# Other example LLM

# gemma = LLMHuggingFace(agent=agent, name='google/gemma-2b-it', parameters={'max_new_tokens': 1}, num_previous_messages=10)
# llama = LLMHuggingFaceAPI(agent=agent, name='meta-llama/Meta-Llama-3.1-8B-Instruct', parameters={}, num_previous_messages=10)
# mixtral = LLMReplicate(agent=agent, name='mistralai/mixtral-8x7b-instruct-v0.1', parameters={}, num_previous_messages=10)

# Intents

yes_to_all_intent = data_labeling_agent.new_intent('yes_to_all_intent', ['yes to all'])
yes_intent = data_labeling_agent.new_intent('yes_intent', ['yes'])
no_intent = data_labeling_agent.new_intent('no_intent', ['no'])

# STATES

initialization_state = data_labeling_agent.new_state('initialization_state', initial=True)
initial_state = data_labeling_agent.new_state('initial_state', ic_config=llm_ic_config)
build_query_state = data_labeling_agent.new_state('build_query_state')
run_query_state = data_labeling_agent.new_state('run_query_state')
fallback_state = data_labeling_agent.new_state('fallback_state')


# STATES BODIES' DEFINITION + TRANSITIONS


def initialization_state_body(session: Session):
    # Establish connection to elasticsearch
    es_host = data_labeling_agent.get_property(ELASTICSEARCH_HOST)
    es_port = data_labeling_agent.get_property(ELASTICSEARCH_PORT)
    es_index = data_labeling_agent.get_property(ELASTICSEARCH_INDEX)
    es_url = f'http://{es_host}:{es_port}'
    es = Elasticsearch([es_url])
    session.set(ELASTICSEARCH, es)
    session.set(INDEX, es_index)
    session.set(YES_TO_ALL, False)
    session.reply('Hello! I am the Data Labeling agent. You can send me requests through the form on the left side, or ask any doubt through the chat input box.')


initialization_state.set_body(initialization_state_body)
initialization_state.go_to(initial_state)


def initial_state_body(session: Session):
    pass


initial_state.set_body(initial_state_body)
initial_state.when_event(ReceiveJSONEvent()).go_to(build_query_state)
initial_state.when_no_intent_matched().go_to(fallback_state)


def build_query_body(session: Session):
    session.reply('Request received. First, I am going to select the documents that match your filters...')
    request = json.loads(session.event.message)
    es: Elasticsearch = session.get(ELASTICSEARCH)
    index: str = session.get(INDEX)
    query = build_query(
        date_from=request[DATE_FROM],
        date_to=request[DATE_TO],
        filters=request[FILTERS]
    )
    session.set(REQUEST, request)
    session.set(QUERY, query)
    num_docs = get_num_docs(
        es_client=es,
        index_name=index,
        query=query
    )
    message = f'There are {num_docs} documents matching your filters. '
    if request[INSTRUCTIONS]:
        message += f'The next step is to determine whether these documents satisfy the instructions you defined. This may take some time since each document is analyzed with an LLM.'
        if not session.get(YES_TO_ALL):
            message += " Do you want to proceed?"
    elif not session.get(YES_TO_ALL):
        message += f'Do you want to proceed assigning them the score/label you selected?'
    session.reply(message)
    if not session.get(YES_TO_ALL):
        websocket_platform.reply_options(session, ['Yes', 'No', 'Yes to all'])


build_query_state.set_body(build_query_body)
build_query_state.when_variable_matches_operation(YES_TO_ALL, operator.eq, True).go_to(run_query_state)
build_query_state.when_intent_matched(yes_intent).go_to(run_query_state)
build_query_state.when_intent_matched(yes_to_all_intent).go_to(run_query_state)
build_query_state.when_intent_matched(no_intent).go_to(initial_state)
build_query_state.when_event(ReceiveJSONEvent()).go_to(build_query_state)


def run_query_body(session: Session):
    if isinstance(session.event, ReceiveTextEvent) and session.event.predicted_intent.intent == yes_to_all_intent:
        session.set(YES_TO_ALL, True)
    es: Elasticsearch = session.get(ELASTICSEARCH)
    index: str = session.get(INDEX)
    query = session.get(QUERY)
    request = session.get(REQUEST)
    if request[INSTRUCTIONS]:
        session.reply('Proceeding with the document analysis...')
        scroll_docs(
            session=session,
            es_client=es,
            index_name=index,
            query=query,
            request=request,
            llm=llm,
            batch_size=1
        )
    else:
        if request[ACTION] == DOCUMENT_RELEVANCE:
            update_document_relevance_query(
                es_client=es,
                index_name=index,
                query=query,
                document_relevance=request[TARGET_VALUE]
            )
        elif request[ACTION] == DOCUMENT_LABELS:
            append_document_label_query(
                es_client=es,
                index_name=index,
                query=query,
                new_label=request[TARGET_VALUE]
            )
        num_docs = get_num_docs(
            es_client=es,
            index_name=index,
            query=query
        )
        session.reply(json.dumps({REQUEST_ID: session.get(REQUEST)[REQUEST_ID], UPDATED_DOCS: num_docs, IGNORED_DOCS: 0, TOTAL_DOCS: num_docs, FINISHED: True}))

    session.reply('✅ Process completed! Ready to listen to your next request.')


run_query_state.set_body(run_query_body)
run_query_state.go_to(initial_state)


def help_body(session: Session):
    session.reply('you need help?')


# help_state.set_body(help_body)


def fallback_body(session: Session):
    response = llm.predict(
f"""
You are an agent used to automatically label documents from an elasticsearch database.
The user sent you a message that couldn't be understood as one of the default actions (intents) of the agent.
Therefore, it jumped to a fallback state. Your task is to generate an appropriate response to the user, if possible.
You don't have access to the elasticsearch database right now (only from the appropriate form in the user's app),
so questions related to the database cannot be properly answered.
To give you some context, you are being used from an app with a form that allows the user to send you requests to label the database documents.
The user can select between setting a 'Document Relevance' score (with possible values being 'relevant', 'not relevant' or 'smoking gun')
or assigning a custom label to a document. The user can set filters to filter the documents where the label or score wants to be applied.
The user can also set 'Instructions', which are natural language prompts that can be used by an LLM to try to find those documents that match
the instructions. The chat messages (like the one that made this interaction happen) are only used to guide the user on how to use the form.
This is the user message: '{session.event.message}'.
"""
    )
    session.reply(response)


fallback_state.set_body(fallback_body)
fallback_state.go_to(initial_state)


# RUN APPLICATION

if __name__ == '__main__':
    data_labeling_agent.run()
