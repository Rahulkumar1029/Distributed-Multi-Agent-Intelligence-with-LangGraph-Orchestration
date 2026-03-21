# Distributed-Multi-Agent-Intelligence-with-LangGraph-Orchestration

---

## 🧠 Overview

This project is a **multi-agent AI system** built using LangGraph that orchestrates multiple specialized agents into a single unified intelligence layer.

Instead of relying on a single AI system, this architecture combines multiple domain-specific agents (Travel, Expense, RAG) and coordinates them through a central reasoning system to solve complex user queries.

The goal is to move from **isolated AI agents → coordinated intelligent systems**.

---

## 🎯 Problem Statement

In real-world systems:

- AI agents are built independently  
- Each agent solves a specific task  
- There is no unified interface to use them together  
- Context is not shared between systems  
- Scaling multiple agents becomes difficult  

This leads to **fragmented intelligence and poor system coordination**.

## 💡 Solution

This project introduces a **multi-agent orchestration system** that:

- Combines multiple AI agents into a single system  
- Dynamically selects the correct agent based on user intent  
- Maintains conversation state using PostgreSQL  
- Enables tool-based reasoning using MCP  
- Supports real-time streaming responses  

👉 Result: A **coordinated AI system instead of isolated tools**

## 🤖 Agents Overview

### ✈️ Bot 1 — Travel Agent
- Provides train and flight information  
- Uses external tools via MCP  
- Handles route planning and travel queries  
![Travel Agent Demo](<img width="1907" height="912" alt="travel_agent" src="https://github.com/user-attachments/assets/877ac1a0-7b7a-410d-a967-dd755c0ab95f" />)

### 💰 Bot 2 — Expense Tracker Agent
- Add, update, delete expenses  
- Category-based tracking  
- Query expenses with filters  
- Structured database interactions  
![Expense Tracker Agent Demo](<img width="1920" height="1080" alt="expense" src="https://github.com/user-attachments/assets/161e8efc-b0fe-44a9-937b-9aa1470cfa54" />
)

### 📚 Bot 3 — RAG Agent
- Retrieval-Augmented Generation  
- Answers queries from industry documents  
- Context-aware knowledge retrieval  
![RAG Agent Demo](<img width="1920" height="1080" alt="rag" src="https://github.com/user-attachments/assets/243c4778-b187-479d-8cbc-929a4ea5ad60" />
)


### 🧠 Bot 4 — Multi-Agent Supervisor (Orchestrator)
- Central decision-making agent  
- Routes queries to appropriate agents  
- Supports multi-step reasoning  
- Can use multiple agents for a single query  
![Multi-Agent Supervisor Demo](<img width="1920" height="1080" alt="Multi_bot" src="https://github.com/user-attachments/assets/e9b06aa6-4527-467d-84f6-d599498b6cea" />
)

## ⚙️ Key Features

- 🔁 Multi-agent orchestration  
- 🧠 Tool-augmented reasoning (MCP)  
- 💾 Persistent conversation memory (PostgreSQL)  
- ⚡ Streaming responses (SSE)  
- 🔄 Dynamic agent routing  
- 📡 LangGraph-based stateful workflows  
- 📚 RAG-based document querying  


## 🧠 Why Multi-Agent Systems?

Multi-agent systems break complex problems into smaller tasks handled by specialized agents and coordinate them efficiently. :contentReference[oaicite:0]{index=0}  

Orchestration ensures all agents collaborate toward a shared goal instead of working independently. :contentReference[oaicite:1]{index=1}  

This leads to:
- Better scalability  
- Improved accuracy  
- Modular system design  

---

## 🧩 Industry Relevance

This architecture is directly applicable in real-world systems where:

- Multiple AI systems need to work together  
- Different domains require specialized intelligence  
- Systems must scale without breaking existing workflows  

Examples:
- Enterprise AI copilots  
- Financial assistants  
- Customer support systems  
- Knowledge management systems  

Multi-agent orchestration allows organizations to move from isolated tools to **coordinated enterprise intelligence systems**. :contentReference[oaicite:2]{index=2}  

## 🛠️ Tech Stack

- Python  
- LangGraph  
- LangChain  
- FastAPI  
- PostgreSQL  
- MCP (Model Context Protocol)  
- Docker  

---

## ⚡ Getting Started

```bash
git clone https://github.com/your-username/repo-name
cd repo-name

pip install -r requirements.txt

