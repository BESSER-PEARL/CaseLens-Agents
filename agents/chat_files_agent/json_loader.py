import json
from datetime import datetime

from agents.chat_files_agent.chat_data import Chat, WhatsAppMessage, User
from app.vars import WHATSAPP


def json_loader(filepath: str):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            chat_type = data['config']['chat_type']
            chat: Chat = Chat(chat_type=chat_type)

            chat.config.container_height = data['config']['container_height']
            chat.config.right_aligned = data['config']['right_aligned']
            chat.config.show_timestamps = data['config']['show_timestamps']
            chat.config.page_size = data['config']['page_size']
            chat.config.view_attachments = data['config']['view_attachments']
            for message_json in data['messages']:
                if chat.config.chat_type == WHATSAPP:
                    message = WhatsAppMessage(
                        id=message_json['id'],
                        user=User(name=message_json['user']),
                        timestamp=datetime.strptime(message_json['timestamp'], "%Y-%m-%d %H:%M:%S"),
                        content=message_json['content']
                    )
                    chat.add_message(message)
            if data['owner']:
                chat.owner = chat.get_user(data['owner'])
            return chat
    except FileNotFoundError:
        print(f"File not found: {filepath}")
    except json.JSONDecodeError:
        print(f"Could not decode JSON in file: {filepath}")