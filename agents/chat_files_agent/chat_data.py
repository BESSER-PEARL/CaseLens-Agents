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

    def __init__(self, user: User, timestamp: datetime, content: str):
        self.user: User = user
        self.content: str = content
        self.timestamp: datetime = timestamp

    @abstractmethod
    def has_attachment(self):
        pass

    @abstractmethod
    def extract_attachment_name(self) -> str | None:
        pass


class WhatsAppMessage(Message):

    def __init__(self, user: User, timestamp: datetime, content: str):
        super().__init__(user=user, timestamp=timestamp, content=content)

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


class Chat:

    def __init__(self, messages: list[Message] = None, owner: User = None):
        if messages is None:
            messages = []
        self.messages: list[Message] = messages
        self.owner: User = owner
        self.users: set[User] = set()
        for message in messages:
            self.users.add(message.user)
        self.config: ChatConfig = ChatConfig(self)

    def add_message(self, message: Message):
        self.messages.append(message)
        self.users.add(message.user)

    def num_messages(self) -> int:
        return len(self.messages)

    def get_messages(self) -> list[Message]:
        ini = (self.config.selected_page - 1) * self.config.page_size
        end = min(ini+self.config.page_size, len(self.messages))
        return self.messages[ini:end]


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
            self.selected_page = int(selected_message / self.page_size) + 1

    def get_selected_date_or_next(self) -> date:
        if not self.selected_date:
            return None
        for message in self.chat.messages:
            if message.timestamp.date() >= self.selected_date:
                return message.timestamp.date()
