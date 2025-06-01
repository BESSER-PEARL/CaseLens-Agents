import re
from abc import ABC, abstractmethod
from datetime import datetime, date


class User:

    def __init__(self, name: str):
        self.name: str = name

    def __eq__(self, other):
        if type(other) is type(self):
            return self.name == other.name
        else:
            return False

    def __hash__(self):
        return hash(self.name)


class Message(ABC):

    def __init__(self, id: int, user: User, timestamp: datetime, content: str):
        self.id: int = id
        self.user: User = user
        self.content: str = content
        self.timestamp: datetime = timestamp
        self.hidden: bool = False

    @abstractmethod
    def has_attachment(self):
        pass

    @abstractmethod
    def extract_attachment_name(self) -> str | None:
        pass

    @abstractmethod
    def to_json(self) -> dict:
        pass


class WhatsAppMessage(Message):

    def __init__(self, id: int, user: User, timestamp: datetime, content: str):
        super().__init__(id=id, user=user, timestamp=timestamp, content=content)

    def has_attachment(self):
        pattern = r'^<attached: .+?>$'
        return bool(re.match(pattern, self.content.strip()))

    def extract_attachment_name(self) -> str | None:
        pattern = r'^<attached: (.+?)>$'
        match = re.match(pattern, self.content.strip())
        if match:
            return match.group(1)
        return None

    def __eq__(self, other):
        return isinstance(other, WhatsAppMessage) and self.user == other.user and self.content == other.content and self.timestamp == other.timestamp

    def __hash__(self):
        return hash((self.user, self.content, self.timestamp))

    def to_json(self) -> dict:
        return {
            'id': self.id,
            'hidden': self.hidden,
            'user': self.user.name,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'content': self.content
        }


class Chat:

    def __init__(self, name: str, chat_type: str, messages: list[Message] = None, owner: User = None):
        if messages is None:
            messages = []
        self.name: str = name
        self.messages: list[Message] = messages
        self.owner: User = owner
        self.users: set[User] = set()
        for message in messages:
            self.users.add(message.user)
        self.config: ChatConfig = ChatConfig(self)
        self.config.chat_type = chat_type

    def add_message(self, message: Message):
        self.messages.append(message)
        self.users.add(message.user)

    def num_messages(self) -> int:
        return len(self.messages)

    def get_messages(self) -> list[Message]:
        ini = (self.config.selected_page - 1) * self.config.page_size
        end = min(ini+self.config.page_size, len(self.messages))
        return self.messages[ini:end]

    def get_user(self, name: str):
        for user in self.users:
            if user.name == name:
                return user
        return None

    def to_json(self):
        return {
            # TODO: Include message index???
            "name": self.name,
            "messages": [message.to_json() for message in self.messages],
            "owner": self.owner.name if self.owner else None,
            "users": [user.name for user in self.users],
            "config": self.config.to_json()
        }

    def to_prompt_format(self):
        chat_str = ""
        for message in self.messages:
            if not message.hidden:
                chat_str += f'{message.id} [{message.timestamp}] {message.user.name}: {message.content}\n'
        return chat_str


class ChatConfig:

    def __init__(
            self,
            chat: Chat,
            container_height: int = 650,
            right_aligned: bool = False,
            show_timestamps: bool = True,
            page_size: int = 100,
            selected_date: date = None,
            selected_message: int = None,
            view_attachments: bool = False
    ):
        self.chat: Chat = chat
        self.chat_type: str = None
        self.container_height: int = container_height
        self.right_aligned: bool = right_aligned
        self.show_timestamps: bool = show_timestamps
        self.page_size: int = page_size
        self._selected_date: date = selected_date
        self._selected_message: int = selected_message
        self.selected_page: int = 1
        self.view_attachments: bool = view_attachments

    @property
    def selected_date(self):
        return self._selected_date

    @selected_date.setter
    def selected_date(self, selected_date: date):
        self._selected_date = selected_date
        if self._selected_date:
            for i, message in enumerate(self.chat.messages):
                if message.timestamp.date() >= self.selected_date:
                    self.selected_page = int(i / self.page_size) + 1
                    return

    @property
    def selected_message(self):
        return self._selected_message

    @selected_message.setter
    def selected_message(self, selected_message: int):
        self._selected_message = selected_message
        if self._selected_message:
            self.selected_page = int((selected_message-1) / self.page_size) + 1

    def get_selected_date_or_next(self) -> date:
        if not self.selected_date:
            return None
        for message in self.chat.messages:
            if message.timestamp.date() >= self.selected_date:
                return message.timestamp.date()

    def to_json(self) -> dict:
        return {
            'chat_type': self.chat_type,
            'container_height': self.container_height,
            'right_aligned': self.right_aligned,
            'show_timestamps': self.show_timestamps,
            'page_size': self.page_size,
            'selected_date': self.selected_date,
            'selected_message': self.selected_message,
            'view_attachments': self.view_attachments
        }
