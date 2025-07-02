# CaseLens Agents

Agents for the CaseLens project. Built with [BESSER Agentic Framework](https://github.com/BESSER-PEARL/BESSER-Agentic-Framework)

## Run the app

### Requirements

- Python >= 3.10
- Recommended: Create a virtual environment
  (e.g. [venv](https://docs.python.org/3/library/venv.html),
  [conda](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html))

```shell
pip install -r requirements.txt
```

```shell
python run.py
```

You can access the application in `http://localhost:8501`

## Deploy with Docker

### 1. Build Docker image

This command uses the file [Dockerfile](Dockerfile)

```shell
docker build -t besser-agents .
```

### 2. Create and run container

This command uses the file [docker-compose.yml](docker-compose.yml)

```shell
docker-compose up -d
```

You can access the application in `http://localhost:8501`

### Volumes

In Docker, a volume is a persistent storage mechanism used to store and share data between containers and the host system,
independent of the container's lifecycle.

This app has 2 volumes, as specified in [docker-compose.yml](docker-compose.yml):

- [.streamlit](.streamlit): contains [secrets.toml](.streamlit/secrets.toml) and [config.toml](.streamlit/config.toml), 
  which store some Streamlit properties (Streamlit is the UI framework of the application) (more info in the official [Streamlit docs](https://docs.streamlit.io/develop/api-reference/configuration/config.toml))
- [data](data): Stores data created by the agents.


The [data](data) volume contains the following:

- [config.ini](data/config.ini): properties for the agents. We can define the following properties here:
  - `nlp.ollama.host = localhost` Host address of the Ollama LLM
  - `nlp.ollama.port = 11434` Port of the Ollama LLM
  - `nlp.ollama.max_tokens = 8000` Maximum number of input tokens for the LLM 
  - `nlp.ollama.model = gemma3:12b` Name of the Ollama LLM ([full list here](https://ollama.com/library))
  - `nlp.hf.tokenizer = google/gemma-2-2b-it` Name of the tokenizer to use (should be the same family of the LLM. ([full list here](https://huggingface.co/models)))
  - `nlp.hf.api_key = YOUR-API-KEY` HuggingFace API Key. Some tokenizers may need authentication and therefore it is necessary to provide this key.
  - `elasticsearch.host = localhost` Host address of the elasticsearch database
  - `elasticsearch.port = 19200` Port of the elasticsearch database
  - `elasticsearch.index = castor-test-enron` Name of the elastiscearch index
- [data_labeling_agent](data/data_labeling_agent) folder: Contains the file [request_history.json](data/data_labeling_agent/request_history.json), which stores the requests done with this agent.
- [chat_files_agent](data/chat_files_agent) folder: Contains the file [chat_notebook.json](data/chat_files_agent/chat_notebook.json),
  which stores the requests done with this agent. Also contains the [chats](data/chat_files_agent/chats) folder.
  All imported chats are processed and exported in JSON format into this folder. The agent actually uses these files to analyze the chat files.

