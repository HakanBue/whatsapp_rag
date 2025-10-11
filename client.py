# client.py
import os, sys, json, asyncio, hashlib
from dotenv import load_dotenv
from prompt import COMMANDS_GROUP_SYSTEM_PROMPT as SYSTEM_PROMPT

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Set OPENAI_API_KEY in your .env")

from openai import OpenAI
oai = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = (
    "You are a helpful WhatsApp assistant. "
    "You can request tools to search contacts, list chats/messages, and send messages/files. "
    "When appropriate, choose and call tools to fulfill the user request. "
    "Be concise and act safely."
)

COMMANDS_CHAT_NAME = "Commands"
POLL_INTERVAL_SEC = 3
STATE_FILE = ".state_commands.json"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
VENV_PYTHON = os.path.join(BASE_DIR, "venv", "bin", "python")  # change to ".venv" if that's your venv
SERVER_MAIN = os.path.join(BASE_DIR, "whatsapp-mcp", "whatsapp-mcp-server", "main.py")

if not os.path.exists(VENV_PYTHON):
    VENV_PYTHON = sys.executable
if not os.path.exists(SERVER_MAIN):
    raise RuntimeError(f"Cannot find server main.py at {SERVER_MAIN}")

from fastmcp import Client

MCP_CONFIG = {
    "mcpServers": {
        "whatsapp": {
            "transport": "stdio",
            "command": VENV_PYTHON,
            "args": ["-u", SERVER_MAIN],
            "env": {},
        }
    }
}

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"seen_ids": []}

def save_state(s):
    with open(STATE_FILE, "w") as f:
        json.dump(s, f)

def pick_tool_name(all_tools, target_suffix):
    names = [t.name for t in all_tools]
    if target_suffix in names:
        return target_suffix
    for n in names:
        if n.endswith("_" + target_suffix) or n.endswith(target_suffix):
            return n
    raise RuntimeError(f"Could not find a tool matching '{target_suffix}'. Available: {names}")

def extract_result_any(call_result):
    sc = getattr(call_result, "structured_content", None)
    if sc is not None:
        if isinstance(sc, dict) and "result" in sc:
            return sc["result"]
        return sc
    d = getattr(call_result, "data", None)
    if hasattr(d, "result"):
        return d.result
    return d

def stable_id_from_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def extract_text_and_id_from_last_message(last_message) -> tuple[str | None, str | None]:
    if isinstance(last_message, dict):
        text = last_message.get("text")
        mid = last_message.get("id")
        if text is None:
            text = json.dumps(last_message, ensure_ascii=False)
        if mid is None:
            mid = stable_id_from_text(json.dumps(last_message, sort_keys=True, ensure_ascii=False))
        return (text.strip() if isinstance(text, str) else str(text)), str(mid)
    elif isinstance(last_message, str):
        return last_message.strip(), stable_id_from_text(last_message)
    else:
        s = json.dumps(last_message, ensure_ascii=False) if not isinstance(last_message, str) else last_message
        return s.strip(), stable_id_from_text(s)

async def run():
    client = Client(MCP_CONFIG)

    async with client:
        await client.ping()

        tools = await client.list_tools()
        print("== Tools exposed by server ==")
        for t in tools:
            print(" -", t.name)

        LIST_CHATS = pick_tool_name(tools, "list_chats")
        GET_CHAT = pick_tool_name(tools, "get_chat")
        SEND_MESSAGE = pick_tool_name(tools, "send_message")

        # Build OpenAI tool specs from the server schemas
        oai_tools = []
        for t in tools:
            schema = t.inputSchema or {"type": "object", "properties": {}, "additionalProperties": False}
            oai_tools.append({
                "type": "function",
                "function": {"name": t.name, "description": t.description or "", "parameters": schema}
            })

        async def call_mcp_tool(tool_call):
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments or "{}")
            res = await client.call_tool(name, args)
            payload = extract_result_any(res)
            return json.dumps(payload, ensure_ascii=False)

        # Resolve Commands chat JID
        res = await client.call_tool(LIST_CHATS, {"include_last_message": True, "limit": 200, "page": 0})
        chats_payload = extract_result_any(res)
        chats_list = chats_payload["result"] if isinstance(chats_payload, dict) and "result" in chats_payload else chats_payload
        if not isinstance(chats_list, list):
            raise RuntimeError(f"list_chats did not return a list; got {type(chats_list)}")

        cmd_chat_jid = None
        for ch in chats_list:
            chat_name = ch.get("name") or ch.get("title") or ""
            if chat_name == COMMANDS_CHAT_NAME:
                cmd_chat_jid = ch.get("jid")
                break
        if not cmd_chat_jid:
            for ch in chats_list:
                chat_name = (ch.get("name") or ch.get("title") or "").lower()
                if COMMANDS_CHAT_NAME.lower() in chat_name:
                    cmd_chat_jid = ch.get("jid")
                    break
        if not cmd_chat_jid:
            raise RuntimeError(f"Could not find a chat named '{COMMANDS_CHAT_NAME}'.")

        state = load_state()
        seen_ids = set(state.get("seen_ids", []))
        print(f"Watching '{COMMANDS_CHAT_NAME}' ({cmd_chat_jid}). Seen IDs: {len(seen_ids)}")

        # main loop — poll get_chat(include_last_message=True)
        while True:
            res = await client.call_tool(GET_CHAT, {"chat_jid": cmd_chat_jid, "include_last_message": True})
            chat_obj = extract_result_any(res)
            if isinstance(chat_obj, dict) and "result" in chat_obj:
                chat_obj = chat_obj["result"]
            if not isinstance(chat_obj, dict):
                raise RuntimeError(f"get_chat did not return an object; got {type(chat_obj)}")

            last_msg_raw = chat_obj.get("last_message")
            text, mid = extract_text_and_id_from_last_message(last_msg_raw)

            if mid and text and mid not in seen_ids:
                print(f"\n[Commands] {text}")

                # ---- IMPORTANT: maintain a single conversation list and
                # append the assistant tool_calls message BEFORE tool messages. ----

                # text currently holds the message content you extracted
                raw = (text or "").strip()

                # strip a leading '!n' command prefix (and any spaces/colon right after it)
                if raw.startswith("!n"):
                    raw = raw[2:].lstrip(" :")

                # optional: remove surrounding quotes if the whole message is quoted
                if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
                    raw = raw[1:-1].strip()

                conversation = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": raw},
                ]

                for _ in range(6):
                    resp = oai.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=conversation,
                        tools=oai_tools,
                        tool_choice="auto",
                        temperature=0.2,
                    )
                    ai_msg = resp.choices[0].message

                    if ai_msg.tool_calls:
                        # 1) append assistant message with tool_calls
                        conversation.append({
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": tc.id,
                                    "type": "function",
                                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                                } for tc in ai_msg.tool_calls
                            ],
                        })
                        # 2) execute each tool and append the corresponding tool message
                        for tc in ai_msg.tool_calls:
                            tool_result_text = await call_mcp_tool(tc)
                            conversation.append({
                                "role": "tool",
                                "tool_call_id": tc.id,
                                "name": tc.function.name,
                                "content": tool_result_text,
                            })
                        # continue loop for possible follow-up tool calls
                        continue
                    else:
                        final_reply = ai_msg.content or "✅ Done."
                        # send final reply into Commands
                        await client.call_tool(SEND_MESSAGE, {
                            "recipient": cmd_chat_jid,
                            "message": final_reply[:2000],
                        })
                        break

                seen_ids.add(mid)
                state["seen_ids"] = list(seen_ids)
                save_state(state)

            await asyncio.sleep(POLL_INTERVAL_SEC)

if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\nbye")

