# You may need to add your working directory to the Python path. To do so, uncomment the following lines of code
# import sys
# sys.path.append("/Path/to/directory/agentic-framework") # Replace with your directory path
import json
import logging

from besser.agent.core.agent import Agent
from besser.agent.core.session import Session
from besser.agent.core.state import State
from besser.agent.exceptions.logger import logger
from besser.agent.nlp.intent_classifier.intent_classifier_configuration import LLMIntentClassifierConfiguration
from besser.agent.nlp.llm.llm_huggingface import LLMHuggingFace
from besser.agent.nlp.llm.llm_huggingface_api import LLMHuggingFaceAPI
from besser.agent.nlp.llm.llm_openai_api import LLMOpenAI
from besser.agent.nlp.llm.llm_replicate_api import LLMReplicate
from elasticsearch import Elasticsearch
from pydantic import BaseModel

from streamlit_ui.pages.elasticsearch_query import build_query, get_num_docs, update_document_relevance_query, \
    append_document_label_query, scroll_docs

# Configure the logging module (optional)
logger.setLevel(logging.INFO)

# Create the agent
agent = Agent('llm_agent')
# Load agent properties stored in a dedicated file
agent.load_properties('config.ini')
# Define the platform your agent will use
websocket_platform = agent.use_websocket_platform(use_ui=False)


class LLMOutput(BaseModel):
    result: bool

# Create the LLM
gpt = LLMOpenAI(
    agent=agent,
    name='gpt-4o-mini',
    parameters={
        # 'max_completion_tokens': 1,
        # 'response_format': {"type": "json_object"}
    },
    num_previous_messages=10
)

# Other example LLM

# gemma = LLMHuggingFace(agent=agent, name='google/gemma-2b-it', parameters={'max_new_tokens': 1}, num_previous_messages=10)
# llama = LLMHuggingFaceAPI(agent=agent, name='meta-llama/Meta-Llama-3.1-8B-Instruct', parameters={}, num_previous_messages=10)
# mixtral = LLMReplicate(agent=agent, name='mistralai/mixtral-8x7b-instruct-v0.1', parameters={}, num_previous_messages=10)


es_host = "localhost"
es_port = "19200"
index_name = "castor-test-enron"

# STATES

initialization_state = agent.new_state('initialization_state', initial=True)
initial_state = agent.new_state('initial_state')
build_query_state = agent.new_state('build_query_state')
run_query_state = agent.new_state('run_query_state')


# Intents

yes_intent = agent.new_intent('yes_intent', ['yes'])
no_intent = agent.new_intent('no_intent', ['no'])


# STATES BODIES' DEFINITION + TRANSITIONS

def global_fallback_body(session: Session):
    session.reply("Sorry, I didn't understand your request")


agent.set_global_fallback_body(global_fallback_body)


def initialization_state_body(session: Session):
    # Establish connection to elasticsearch
    es_url = f'http://{es_host}:{es_port}'
    es = Elasticsearch([es_url])
    session.set('es', es)


initialization_state.set_body(initialization_state_body)
initialization_state.go_to(initial_state)


def initial_state_body(session: Session):
    pass


initial_state.set_body(initial_state_body)
initial_state.when_no_intent_matched_go_to(build_query_state)


def build_query_body(session: Session):
    message = json.loads(session.message)
    es: Elasticsearch = session.get('es')
    query = build_query(
        date_from=message['date_from'],
        date_to=message['date_to'],
        filters=message['filters']
    )
    session.set('request', message)
    session.set('query', query)
    num_docs = get_num_docs(
        es_client=es,
        index_name=index_name,
        query=query
    )
    websocket_platform.reply(session, f'There are {num_docs} documents matching your filters. Do you want to proceed with LLM?')
    # TODO: CHECK HOW MANY OF THEM HAVE ALREADY THE TARGET VALUE?
    websocket_platform.reply_options(session, ['Yes', 'No'])


build_query_state.set_body(build_query_body)
build_query_state.when_intent_matched_go_to(yes_intent, run_query_state)
build_query_state.when_intent_matched_go_to(no_intent, initial_state)
build_query_state.when_no_intent_matched_go_to(build_query_state)  # New request


def run_query_body(session: Session):
    es: Elasticsearch = session.get('es')
    query = session.get('query')
    request = session.get('request')
    if request['semantic_instructions']:
        scroll_docs(
            session=session,
            es_client=es,
            index_name=index_name,
            query=query,
            request=request,
            llm=gpt,
            batch_size=1
        )
    else:
        if request['action'] == 'DOCUMENT_RELEVANCE':
            update_document_relevance_query(
                es_client=es,
                index_name=index_name,
                query=query,
                document_relevance=request['target_value']
            )
        elif request['action'] == 'DOCUMENT_LABELS':
            append_document_label_query(
                es_client=es,
                index_name=index_name,
                query=query,
                new_label=request['target_value']
            )


run_query_state.set_body(run_query_body)
run_query_state.go_to(initial_state)


# RUN APPLICATION

if __name__ == '__main__':
    agent.run()