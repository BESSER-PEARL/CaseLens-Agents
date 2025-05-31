# You may need to add your working directory to the Python path. To do so, uncomment the following lines of code
# import sys
# sys.path.append("/Path/to/directory/agentic-framework") # Replace with your directory path
import json
import logging
import os

from besser.agent.core.agent import Agent
from besser.agent.core.entity.entity import Entity
from besser.agent.core.session import Session
from besser.agent.exceptions.logger import logger
from besser.agent.library.transition.events.base_events import ReceiveJSONEvent
from besser.agent.nlp.intent_classifier.intent_classifier_configuration import LLMIntentClassifierConfiguration
from besser.agent.nlp.intent_classifier.intent_classifier_prediction import IntentClassifierPrediction
from besser.agent.nlp.llm.llm_openai_api import LLMOpenAI

from agents.chat_files_agent.json_loader import json_loader
from app.vars import *

# Configure the logging module (optional)
logger.setLevel(logging.INFO)

# Create the agent
chat_files_agent = Agent('chat_files_agent')
# Load agent properties stored in a dedicated file
chat_files_agent.load_properties('agents/config.ini')
# Define the platform your agent will use
websocket_platform = chat_files_agent.use_websocket_platform(use_ui=False)


# Create the LLM
llm = LLMOpenAI(
    agent=chat_files_agent,
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

# Intents and entities

topic_entity = Entity(
    name='topic',
    description='A topic'
)

find_topic_intent = chat_files_agent.new_intent(
    name='find_topic_intent',
    description='The user wants to find a specific topic or message in a WhatsApp conversation. The target topic or message is provided in the user query explicitly.'
)
find_topic_intent.parameter('topic', 'TOPIC', topic_entity)

clean_chat_intent = chat_files_agent.new_intent(
    name='clean_chat_intent',
    description='The user wants to clean a WhatsApp conversation (i.e., remove messages that are irrelevant for him/her investigation).'
)
clean_chat_intent.parameter('topic', 'TOPIC', topic_entity)

# STATES

initialization_state = chat_files_agent.new_state('initialization_state', initial=True)
initial_state = chat_files_agent.new_state('initial_state', ic_config=llm_ic_config)
store_chat_state = chat_files_agent.new_state('store_chat_state')
find_topic_state = chat_files_agent.new_state('find_topic_state')
clean_chat_state = chat_files_agent.new_state('clean_chat_state')
fallback_state = chat_files_agent.new_state('fallback_state')


# STATES BODIES' DEFINITION + TRANSITIONS


def initialization_body(session: Session):
    session.reply('Welcome to the chat files agent')


initialization_state.set_body(initialization_body)
initialization_state.go_to(initial_state)


def initial_body(session: Session):
    pass


initial_state.set_body(initial_body)
initial_state.when_intent_matched(find_topic_intent).go_to(find_topic_state)
# initial_state.when_intent_matched(clean_chat_intent).go_to(find_topic_state)  # TODO: IMPLEMENT THIS
initial_state.when_event(ReceiveJSONEvent()).go_to(store_chat_state)  # TODO: We can add condition to check json content
initial_state.when_no_intent_matched().go_to(fallback_state)


def store_chat_body(session: Session):
    chat_file = json.loads(session.event.message)[CHAT]
    file_path = str(os.path.join("agents/chat_files_agent/chats", chat_file))
    chat = json_loader(file_path)
    session.set(CHAT, chat)
    session.reply(f"I received your chat file '{chat_file}' successfully")


store_chat_state.set_body(store_chat_body)
store_chat_state.go_to(initial_state)


def find_topic_body(session: Session):
    predicted_intent: IntentClassifierPrediction = session.event.predicted_intent
    topic = predicted_intent.get_parameter('topic').value
    session.reply(f'I will try to find messages talking about "{topic}"...')
    answer = llm.predict(
        system_message='Your will receive a WhatsApp conversation in JSON format (it can be in any language, or combining some languages), and a topic. Your job is to identify those messages talking about that topic. Return ONLY a list containing the message indexes.',
        message=f'Topic: {topic}\n{session.get(CHAT).to_prompt_format()}'
    )
    session.reply('Done!')
    session.reply(json.dumps({MESSAGE_IDS: answer}))


find_topic_state.set_body(find_topic_body)
find_topic_state.go_to(initial_state)


def clean_chat_body(session: Session):
    predicted_intent: IntentClassifierPrediction = session.event.predicted_intent
    topic = predicted_intent.get_parameter('topic').value
    session.reply(f'I will hide messages talking about "{topic}"...')
    answer = llm.predict(
        system_message='Your will receive a WhatsApp conversation in JSON format (it can be in any language, or combining some languages), and a topic. Your job is to identify those messages talking about that topic. Return ONLY a list containing the message indexes.',
        message=f'Topic: {topic}\n{session.get(CHAT).to_prompt_format()}'
    )
    session.reply('Done!')
    session.reply(json.dumps({'message_ids': answer}))


clean_chat_state.set_body(clean_chat_body)
clean_chat_state.go_to(initial_state)


def fallback_body(session: Session):
    message: str = session.event.message
    answer = llm.predict(
        system_message='Your will receive a WhatsApp conversation and a request. Please, answer properly to the request based on the content of the WhatsApp conversation.',
        message=message + f'\n{session.get(CHAT).to_prompt_format()}'
    )
    session.reply(answer)


fallback_state.set_body(fallback_body)
fallback_state.go_to(initial_state)


# RUN APPLICATION

if __name__ == '__main__':
    chat_files_agent.run()
