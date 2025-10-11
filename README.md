WhatsApp MCP Bot
====================

This project provides a self-hosted WhatsApp Assistant powered by the Model Context Protocol (MCP) and the OpenAI API.
It lets you interact with an AI via WhatsApp — send messages, fetch contacts, and automate tasks — all running locally or on your own VPS.

-------------------------------------------------------------------------------

Overview
--------

This repository combines:

- client.py  
  A FastMCP Python client that communicates with the MCP server, forwards WhatsApp messages to an LLM, and executes tool calls.

- prompt.py  
  Defines the system prompt and tuning for how the LLM uses tools such as list_messages, search_contacts, and send_message.

- whatsapp-mcp/  
  A modified version of the original "whatsapp-mcp" project (Go-based bridge + Python MCP server).
  Original project: https://github.com/lharries/whatsapp-mcp  
  The client automatically starts the MCP server as a subprocess — you do NOT need to run it manually.

------------------------------------------------------------------------------

Origin and modifications
------------------------

This project is based on the open-source "whatsapp-mcp" repository by markormesher / lharries.  
Original repository: https://github.com/lharries/whatsapp-mcp  
Upstream commit used as base: 7d6a06dcdce1f01dfb24f60e1030d5efba9f3b88  

Changes made in this fork include:

- Modified whatsapp-mcp-server/main.py to return deterministic JSON responses compatible with FastMCP.  
- Simplified message parsing for cleaner LLM integration.  
- Added client.py to automate tool discovery, message polling, and AI-driven actions.  
- Added prompt.py for better tool usage guidance.  
- .env configuration
- The client now automatically starts and manages the MCP server process.  

The goal of the modifications were simply allowing communication between the mcp server and a self written MCP Client using FastMCP 2

-------------------------------------------------------------------------------

# Example 
EXAMPLE IMAGE PLACEHOLDER

---------------

Getting started
---------------

1. Prerequisites

- Python 3.10 or newer  
- Go installed (for the bridge)  
- An OpenAI API key  
- A WhatsApp account linked to WhatsApp Web  

## Setup

### 1. Clone and set up the environment
git clone https://github.com/HakanBue/whatsapp_rag.git
cd whatsapp_rag

### create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

### install dependencies
```bash
pip install -r requirements.txt
```
### 2. Create a .env file in the project root and add your OpenAI API key:
```bash
OPENAI_API_KEY=sk-yourkeyhere
```
### 3. Run the project

- The Go bridge connects WhatsApp with the Python server.

- The Python client controls the LLM and orchestrates tool calls.

### Run the Go bridge
```bash
cd whatsapp-mcp/whatsapp-bridge
go run main.go
```

### In another terminal
```bash
cd ~/whatsapp_rag
source .venv/bin/activate
python client.py
```

**That’s it!** The client will automatically connect to the bridge and MCP server, discover tools, and respond to commands in your WhatsApp “Commands” group.

### Interact with the bot
- Create a new group in WhatsApp with just yourself in it and call it "Commands"

- Use your WhatsApp “Commands” group to send messages, for example:

- **Input:** !n send a message to 012345678 saying "Hello from MCP!" **Note the !n prefix (might be changed later)**
- **Output:** The message "Hello from MCP!" has been successfully sent to 012345678

-------------------------------------------------------------------------------

Future (planned)
----------------

- RAG Integration
- Containers for bridge, server, and client + Docker Compose for one-command setup
- Contact name resolution using search_contacts  
- Logging improvements  
- Optional LLM model / provider selection
- overall QoL features 

-------------------------------------------------------------------------------

License and attribution
-----------------------

The original "whatsapp-mcp" project is licensed under the MIT License.
Your modifications retain this license.

When redistributing, please include attribution:

"This project is based on 'whatsapp-mcp' (commit 7d6a06dcdce1f01dfb24f60e1030d5efba9f3b88)
by markormesher/lharries, modified by HakanBue in 2025."

-------------------------------------------------------------------------------

Credits
-------

Original project: https://github.com/lharries/whatsapp-mcp (MIT licensed)
Integration, MCP client, and automation logic by HakanBue, 2025.

