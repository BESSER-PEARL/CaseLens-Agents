# Streamlit session_state keys
from besser.agent.core.property import Property

AGENT_DATA_LABELING = 'agent_data_labeling'
AGENT_CHAT_FILES = 'agent_chat_files'
AGENTS = [
    AGENT_DATA_LABELING,
    AGENT_CHAT_FILES
]
AGENT_WEBSOCKET_PORT = 'agent_websocket_port'

ASSISTANT = 'assistant'
HISTORY = 'history'
QUEUE = 'queue'
SESSION_MONITORING = 'session_monitoring'
SUBMIT_FILE = 'submit_file'
SUBMIT_TEXT = 'submit_text'
SUBMIT_AUDIO = 'submit_audio'
USER = 'user'
WEBSOCKET = 'websocket'
SCREEN_DATA = 'screen_data'

# Time interval to check if a streamlit session is still active, in seconds
SESSION_MONITORING_INTERVAL = 1

# New agent messages are printed with a typing effect. This is the time between words being printed, in seconds
TYPING_TIME = 0.05

ELASTICSEARCH = 'elasticsearch'
INSTRUCTIONS = 'instructions'
INSTRUCTIONS_CHECKBOXES = 'instructions_checkboxes'
FILTERS_CHECKBOXES = 'filters_checkboxes'
PROGRESS_DATA_LABELING = 'progress_data_labeling'
PROGRESS_CHAT_FILES = 'progress_chat_files'
INITIAL_TIME = 'initial_time'

# Progress bar
FINISHED = 'finished'
TIME = 'time'
# Data labeling progress bar
UPDATED_DOCS = 'updated_docs'
IGNORED_DOCS = 'ignored_docs'
TOTAL_DOCS = 'total_docs'
# Chat files progress bar
TOTAL_MESSAGES = 'total_messages'
PROCESSED_MESSAGES = 'processed_messages'

# Elasticsearch index fields
DOCUMENT_RELEVANCE = 'DOCUMENT_RELEVANCE'
DOCUMENT_LABELS = 'DOCUMENT_LABELS'
DATE_CREATED = 'DATE_CREATED'
SUBJECT = 'SUBJECT'
CONTENT = 'CONTENT'
FROM = 'FROM'
TO = 'TO'

# Request
REQUEST_ID = 'id'
ACTION = 'action'
TARGET_VALUE = 'target_value'
DATE_FROM = 'date_from'
DATE_TO = 'date_to'
FILTERS = 'filters'
FIELD = 'field'
OPERATOR = 'operator'
VALUE = 'value'
TEXT = 'text'
TIMESTAMP = 'timestamp'
document_relevance_dict = {
    2: '🔫 Smoking gun',
    1: '👍 Relevant',
    -1: '👎 Not relevant'
}
action_dict = {
    DOCUMENT_RELEVANCE: 'Document Relevance',
    DOCUMENT_LABELS: 'Document Labels'
}

INDEX = 'index'
QUERY = 'query'
REQUEST = 'request'
YES_TO_ALL = 'yes_to_all'
ELASTICSEARCH_CONNECTION_ERROR = 'elasticsearch_connection_error'


EQUALS = 'equals'
DIFFERENT = 'different'
CONTAINS = 'contains'
STARTS_WITH = 'starts with'
REGEXP = 'regexp'
FUZZY = 'fuzzy'

INSTRUCTION_INPUT = 'instruction_input'
INSTRUCTION_FIELD = 'instruction_field'

FILTER_FIELD = 'filter_field'
FILTER_OPERATOR = 'filter_operator'
FILTER_VALUE = 'filter_value'

DATE_FORMAT = '%Y-%m-%d'


ELASTICSEARCH_HOST = Property('elasticsearch', 'elasticsearch.host', str, None)
ELASTICSEARCH_PORT = Property('elasticsearch', 'elasticsearch.port', int, None)
ELASTICSEARCH_INDEX = Property('elasticsearch', 'elasticsearch.index', str, None)


# Pages

CURRENT_PAGE = 'current_page'
HOME = 'Home'
DATA_LABELING = 'Data Labeling'
CHAT_FILES = 'Chat Files'
DASHBOARD = 'Dashboard'
SETTINGS = 'Settings'


REQUEST_HISTORY_FILE = 'request_history_file'
CHAT_NOTEBOOK_FILE = 'chat_notebook_file'
CHATS_DIRECTORY = 'chats_directory'


CHAT = 'chat'
CHAT_NAME = 'chat_name'
MESSAGE_IDS = 'message_ids'
ENTRY_TYPE = 'entry_type'
ENABLED = 'enabled'
TOPIC = 'topic'
TASK = 'task'
FIND_TOPIC = 'find_topic'
HIDE_TOPIC = 'hide_topic'
NOTEBOOK_SELECTED_TOPIC = 'notebook_selected_topic'
CHAT_PAGE = 'chat_page'
ATTACHMENTS = 'attachments'
WHATSAPP = 'WhatsApp'

CHAT_TYPES = [
    WHATSAPP
]
