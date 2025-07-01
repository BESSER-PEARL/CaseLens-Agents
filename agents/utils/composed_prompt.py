import json
import re

from besser.agent.core.session import Session
from besser.agent.nlp.llm.llm import LLM

from agents.chat_files_agent.chat_data import Chat
from agents.utils.token_count import token_count
from app.vars import *


def composed_prompt(session: Session, llm: LLM, chat: Chat, max_tokens: int, tokenizer, chunk_prompt: str, final_prompt: str = None, overlap: int = 0):
    chunk_answers: list[str] = []
    total_messages = chat.num_messages()
    start_message: int = 0
    end_message: int = 1  # placeholder
    chunk_prompt_tokens = token_count(tokenizer, chunk_prompt)
    while start_message <= end_message:
        chat_str, end_message = chat.to_prompt_format(start_message, max_tokens - chunk_prompt_tokens, tokenizer)
        if end_message < total_messages - 1 or start_message > 0:
            # Only show progress bar when there are > 1 chunks
            session.reply(json.dumps({TOTAL_MESSAGES: total_messages, PROCESSED_MESSAGES: start_message, FINISHED: False}))
        chunk_answers.append(llm.predict(
            system_message=chunk_prompt,
            message=chat_str
        ))
        if (start_message >= end_message - overlap) or (end_message == total_messages - 1):
            # Finished
            break
        start_message = end_message - overlap
    if final_prompt:
        if len(chunk_answers) == 1:
            # Skip final prompt
            return chunk_answers[0]
        final_message = ''
        for i, chunk_answer in enumerate(chunk_answers):
            final_message += f"Chunk {i}:\n{chunk_answer}\n"
        # TODO: CHECK LENGTH OF FINAL MESSAGE < MAX_TOKENS
        answer = llm.predict(
            system_message=final_prompt,
            message=final_message
        )
    else:
        answer = chunk_answers
    session.reply(json.dumps({TOTAL_MESSAGES: total_messages, PROCESSED_MESSAGES: total_messages, FINISHED: True}))
    return answer


def extract_numbers(s: str) -> list[int]:
    return [int(num) for num in re.findall(r'\d+', s)]
