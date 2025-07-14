# You may need to add your working directory to the Python path. To do so, uncomment the following lines of code
# import sys
# sys.path.append("/Path/to/directory/agentic-framework") # Replace with your directory path
import ast
import json
import logging
import os

import tiktoken
from besser.agent import nlp
from besser.agent.core.agent import Agent
from besser.agent.core.entity.entity import Entity
from besser.agent.core.session import Session
from besser.agent.exceptions.logger import logger
from besser.agent.library.transition.events.base_events import ReceiveJSONEvent
from besser.agent.nlp.intent_classifier.intent_classifier_configuration import LLMIntentClassifierConfiguration
from besser.agent.nlp.intent_classifier.intent_classifier_prediction import IntentClassifierPrediction
from besser.agent.nlp.llm.llm_openai_api import LLMOpenAI
from huggingface_hub import login
from transformers import AutoTokenizer

from agents.chat_files_agent.json_loader import json_loader
from agents.utils.composed_prompt import composed_prompt, extract_numbers, remove_duplicates
from agents.utils.llm_ollama import LLMOllama, OLLAMA_MODEL, HF_TOKENIZER, OLLAMA_MAX_TOKENS
from app.vars import *

# Configure the logging module (optional)
logger.setLevel(logging.INFO)

# Create the agent
chat_files_agent = Agent('chat_files_agent')
# Load agent properties stored in a dedicated file
chat_files_agent.load_properties('data/config.ini')
# Define the platform your agent will use
websocket_platform = chat_files_agent.use_websocket_platform(use_ui=False)


llm_name = chat_files_agent.get_property(OLLAMA_MODEL)
max_tokens = chat_files_agent.get_property(OLLAMA_MAX_TOKENS)

# Create the LLM
llm = LLMOllama(
    agent=chat_files_agent,
    name=llm_name,
    parameters={
        # 'max_completion_tokens': 1,
        # 'response_format': {"type": "json_object"}
    }
)

if isinstance(llm, LLMOpenAI):
    tokenizer = tiktoken.encoding_for_model(llm.name)
elif isinstance(llm, LLMOllama):
    if chat_files_agent.get_property(nlp.HF_API_KEY):
        login(chat_files_agent.get_property(nlp.HF_API_KEY))
    tokenizer = AutoTokenizer.from_pretrained(chat_files_agent.get_property(HF_TOKENIZER))
else:
    tokenizer = None

llm_ic_config = LLMIntentClassifierConfiguration(
    llm_name=llm_name,
    parameters={},
    use_intent_descriptions=True,
    use_training_sentences=False,
    use_entity_descriptions=True,
    use_entity_synonyms=False
)
chat_files_agent.set_default_ic_config(llm_ic_config)

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
    description='The user wants to clean a WhatsApp conversation (i.e., remove messages that are irrelevant for him/her investigation). The target topic or message is provided in the user query explicitly.'
)
clean_chat_intent.parameter('topic', 'TOPIC', topic_entity)

fallback_intent = chat_files_agent.new_intent(
    name='fallback_intent',
    description='Any other request that is not linked to the other intents'
)

# STATES

initialization_state = chat_files_agent.new_state('initialization_state', initial=True)
initial_state = chat_files_agent.new_state('initial_state')
store_chat_state = chat_files_agent.new_state('store_chat_state')
find_topic_state = chat_files_agent.new_state('find_topic_state')
clean_chat_state = chat_files_agent.new_state('clean_chat_state')
fallback_state = chat_files_agent.new_state('fallback_state')


# STATES BODIES' DEFINITION + TRANSITIONS


def initialization_body(session: Session):
    session.reply('Welcome to the chat files agent. Import a chat to start exploring it!')


initialization_state.set_body(initialization_body)
initialization_state.go_to(initial_state)


def initial_body(session: Session):
    pass


initial_state.set_body(initial_body)
initial_state.when_event(ReceiveJSONEvent()).go_to(store_chat_state)  # TODO: We can add condition to check json content
initial_state.when_intent_matched(find_topic_intent).go_to(find_topic_state)
# initial_state.when_intent_matched(clean_chat_intent).go_to(find_topic_state)  # TODO: IMPLEMENT THIS
initial_state.when_intent_matched(fallback_intent).go_to(fallback_state)
# initial_state.when_no_intent_matched().go_to(fallback_state)


def store_chat_body(session: Session):
    chat_file = json.loads(session.event.message)[CHAT]
    file_path = str(os.path.join("data/chat_files_agent/chats", chat_file))
    chat = json_loader(file_path)
    session.set(CHAT, chat)
    session.reply(f"I received your chat file '{chat_file}' successfully")


store_chat_state.set_body(store_chat_body)
store_chat_state.go_to(initial_state)


def find_topic_body(session: Session):
    if not session.get(CHAT):
        session.reply('Please, load a chat first')
        return
    predicted_intent: IntentClassifierPrediction = session.event.predicted_intent
    topic = predicted_intent.get_parameter('topic').value
    if not topic:
        session.reply("I think you want to find messages about some topic, but I couldn't understand which topic. Could you give me more details?")
        return
    session.reply(f'I will try to find messages talking about "{topic}"...')
    answers = composed_prompt(
        session=session,
        llm=llm,
        chat=session.get(CHAT),
        max_tokens=3000,
        tokenizer=tokenizer,
        chunk_prompt=f'Your will receive a WhatsApp conversation (it can be in any language, or combining some languages). Your job is to identify those messages talking about "{topic}". This is the original user query: "{session.event.message}"\nReturn ONLY a list of integers containing the message indexes (The numbers preceding the messages indicate their indexes, so use that numbers in your answer)',
        final_prompt=None,
        overlap=0
    )
    message_ids = []
    for answer in answers:
        message_ids.extend(extract_numbers(answer))
    message_ids = remove_duplicates(message_ids)
    if message_ids:
        session.reply(json.dumps({TASK: FIND_TOPIC, CHAT_NAME: session.get(CHAT).name, TOPIC: topic, MESSAGE_IDS: message_ids}))
        session.reply('Done! Go to the notebook to see the messages I identified.')
    else:
        session.reply(f'I could not find any message talking about {topic}.')


find_topic_state.set_body(find_topic_body)
find_topic_state.go_to(initial_state)


def clean_chat_body(session: Session):
    if not session.get(CHAT):
        session.reply('Please, load a chat first')
        return
    predicted_intent: IntentClassifierPrediction = session.event.predicted_intent
    topic = predicted_intent.get_parameter('topic').value
    if not topic:
        session.reply("I think you want to hide messages about some topic, but I couldn't understand which topic. Could you give me more details?")
        return
    session.reply(f'I will try to hide messages talking about "{topic}"...')
    answers = composed_prompt(
        session=session,
        llm=llm,
        chat=session.get(CHAT),
        max_tokens=3000,
        tokenizer=tokenizer,
        chunk_prompt=f'Your will receive a WhatsApp conversation (it can be in any language, or combining some languages). Your job is to identify those messages talking about "{topic}". This is the original user query: "{session.event.message}"\nReturn ONLY a list of integers containing the message indexes (The numbers preceding the messages indicate their indexes, so use that numbers in your answer)',
        final_prompt=None,
        overlap=0
    )
    message_ids = []
    for answer in answers:
        message_ids.extend(extract_numbers(answer))
    message_ids = remove_duplicates(message_ids)
    if message_ids:
        session.reply(json.dumps({TASK: HIDE_TOPIC, CHAT_NAME: session.get(CHAT).name, TOPIC: topic, MESSAGE_IDS: message_ids}))
        session.reply(f"Done! I hid the messages talking about '{topic}'. You can undo this from the notebook.")
    else:
        session.reply(f'I could not find any message talking about {topic}.')


clean_chat_state.set_body(clean_chat_body)
clean_chat_state.go_to(initial_state)


def fallback_body(session: Session):
    if not session.get(CHAT):
        session.reply('Please, load a chat first')
        return
    message: str = session.event.message
    answer = composed_prompt(
        session=session,
        llm=llm,
        chat=session.get(CHAT),
        max_tokens=max_tokens,
        tokenizer=tokenizer,
        chunk_prompt=f"Your will receive a WhatsApp conversation (it can be in any language, or combining some languages). Do the following task based on the conversation content: {message}",
        final_prompt="You job is to combine the following LLM-generated answers. The original prompt was too big for the context length and was divided into chunks. Now, you must combine the answer the LLM gave on each chunk into a single one, keeping it coherent and avoiding duplicated content in your final answer. Don't mention the chunk partitions in your answer.",
        overlap=3
    )
    session.reply(answer)


fallback_state.set_body(fallback_body)
fallback_state.go_to(initial_state)


# RUN APPLICATION

if __name__ == '__main__':
    chat_files_agent.run()
