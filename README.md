# LangGraph-Real-Time-Web-Scraping-Agent

https://github.com/user-attachments/assets/08c398c9-8102-4890-885e-425631fdbdfe

This project is a 2-file, real-time web chat application. It uses **LangGraph** to create a stateful agent that can browse the internet using the **Tavily Search API** to answer user questions.

The backend is built with **FastAPI** and streams responses using Server-Sent Events (SSE). The frontend is a single, self-contained **HTML file** using **Tailwind CSS** for styling and vanilla JavaScript to handle the real-time chat interface.

## 🚀 Features

  * **Live Web Search**: The agent can answer questions about recent events, weather, news, and more by using the Tavily search tool.
  * **Real-Time Streaming**: Responses stream from the agent token-by-token.
  * **Agent "Thinking" UI**: The frontend shows the agent's internal process, including when it's "searching" and the results it finds.
  * **Conversation Memory**: The agent uses LangGraph's built-in checkpointing to remember the chat history and answer follow-up questions.
  * **Minimalist Stack**: No complex frontend frameworks. Just FastAPI + LangGraph on the backend and a single HTML/JS file on the frontend.

-----

## 🛠️ How It Works

1.  **Frontend (`index.html`):** The user sends a message. The JavaScript uses `EventSource` to connect to the FastAPI backend.
2.  **API (`app.py`):** The `/chat_stream` endpoint receives the message.
3.  **LangGraph (`app.py`):** The message is passed to the LangGraph agent.
      * **Model Node**: The LLM (e.g., GPT-4o) analyzes the prompt. It decides if it can answer directly or if it needs to search the web.
      * **Router Node**: If the LLM requests a tool, the graph routes to the `tool_node`.
      * **Tool Node**: The agent executes the `tavily_search_results_json` tool with the user's query.
      * **Model Node**: The search results are passed back to the LLM, which then generates a final, comprehensive answer.
4.  **Streaming (SSE):** Throughout this process, the backend sends events to the frontend:
      * `checkpoint`: Sends the new conversation ID.
      * `search_start`: Tells the UI the agent is searching (and shows the query).
      * `search_results`: Sends the URLs the agent found.
      * `content`: Streams the LLM's final answer.
      * `end`: Signals the end of the response.

-----

## ⚙️ Setup and Installation

### 1\. Project Files

You only need two files for this project:

  * `app.py`: The complete backend (FastAPI, LangGraph, and Tavily tool).
  * `index.html`: The complete frontend (HTML, Tailwind CSS, and JavaScript).

### 2\. Install Dependencies

Install all the required Python packages:

```bash
pip install "langgraph[all]" langchain-openai langchain-community tavily-python fastapi uvicorn "sse-starlette" python-dotenv
```

### 3\. Set Environment Variables

This project requires API keys from both OpenAI and Tavily. Create a file named `.env` in the same directory as your `app.py`.

**.env**

```
OPENAI_API_KEY=sk-YourOpenAIKey...
TAVILY_API_KEY=tvly-YourTavilyKey...
```

-----

## 🏃‍♂️ How to Run

### Step 1: Start the Backend Server

Run the `app.py` file from your terminal:

```bash
python app.py
```

The server will start on `http://127.0.0.1:8000`.

### Step 2: Open the Frontend

**Simply open the `index.html` file in your web browser** (e.g., by double-clicking it).

The JavaScript in the file is already set up to connect to the backend server.

### Step 3: Start Chatting\!

You can now ask questions that require real-time web access.

**Example Questions:**

  * "What's the weather in New York today?"
  * "Who won the last F1 race?"
  * "Can you summarize the latest news about AI?"
  * "What are the top-rated restaurants near me?"
