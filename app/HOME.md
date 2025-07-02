# 🧠 CaseLens AI Agents

This project contains three AI-powered agents designed to assist with various data-related tasks, including automatic
document labeling, conversational data exploration, and (in progress) data visualization. Each agent leverages LLMs
(Large Language Models) to interact with users in natural language and provide intelligent assistance.

- Project source code: [https://github.com/BESSER-PEARL/CaseLens-Agents](https://github.com/BESSER-PEARL/CaseLens-Agents)
- Built with [BESSER Agentic Framework](https://github.com/BESSER-PEARL/BESSER-Agentic-Framework)

## 🔧 Agents Overview

### 1. 🏷️ Data Labeling Agent

Automatically label documents stored in an Elasticsearch database, based on user-provided requirements.

**Input**: Request containing the filtering criteria, which can include structured metadata filtering or natural language instructions.

**Process**: The agent uses an LLM to understand the criteria and classify documents accordingly by communicating with the Elasticsearch Database.

**Output**: Labeled documents enriched with metadata.

✅ Ideal for semi-automated dataset enrichment and classification tasks.

### 2. 💬 Chat Files Exploration Agent

Explore and query conversation data (e.g., WhatsApp exports) using natural language.

**Use Case 1: Topic Detection**

- Ask about a specific topic.

- The LLM searches the conversation and returns relevant messages.

- Results are stored in a searchable notebook for review.

**Use Case 2: General Query Fallback**

- When no topic is specified, the LLM tries to answer based on the best matching content in the conversation.

**🔜 Planned:**

- Message Cleaning Intent: Automatically identify and hide messages unrelated to a given topic, allowing users to focus on what matters.

### 3. 📊 (WIP) Data Visualization Agent

Still under development, this agent will provide interactive dashboards and visualizations for:

- Label distribution

- Most accessed or popular documents

- Insights from chat files (message count, topic trends, etc.)

🔄 This agent aims to make exploration and monitoring of your labeled datasets and conversation insights visual and intuitive.

