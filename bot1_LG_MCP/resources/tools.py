from langchain_core.tools import tool
from langchain_core.messages import BaseMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_community.tools import DuckDuckGoSearchResults, YouTubeSearchTool

search_tool = DuckDuckGoSearchResults()
youtube_tool = YouTubeSearchTool()

client = MultiServerMCPClient(
    {
        "railway": {
            "command": "node",
            "args": [
                "C:/Users/rahul/Desktop/mcp_server/indian-railways-mcp/build/index.js"
            ],
            "transport": "stdio",
        },
        "google-flights": {
            "command": "docker",
            "args": ["run", "-i", "--rm", "mcp/google-flights"],
            "transport": "stdio"
        },
        "openbnb-airbnb": {
            "command": "docker",
            "args": [
                "run",
                "-i",
                "--rm",
                "mcp/openbnb-airbnb"
            ],
            "transport": "stdio"
        }
    }
)

@tool
def internet_search(query: str) -> str:
    """
    use this tool for any real time information and Search the internet for real-time information.
    """
    return search_tool.run(query)


@tool
def youtube_search(query: str) -> str:
    """
    Search YouTube for videos.
    """
    return youtube_tool.run(query)


# FINAL FUNCTION YOU WANT
async def get_all_tools():
    try:
        mcp_tools = await client.get_tools()
        tools=mcp_tools + [internet_search, youtube_search]
        return tools
    except Exception as e:
        print(f"Error: {e}")
        return []


def extract_text(content) -> str:
    """
    Convert ANY LLM output into plain text.
    Works with LangChain, Gemini, tool outputs, nested structures.
    """

    # simple string
    if isinstance(content, str):
        return content

    # LangChain message
    if isinstance(content, BaseMessage):
        return extract_text(content.content)

    # list output (Gemini responses)
    if isinstance(content, list):
        texts = []
        for item in content:
            text = extract_text(item)
            if text:
                texts.append(text)
        return " ".join(texts)

    # dict output
    if isinstance(content, dict):

        if "text" in content:
            return str(content["text"])

        if "content" in content:
            return extract_text(content["content"])

        if "message" in content:
            return extract_text(content["message"])

        # fallback: join values
        values = []
        for v in content.values():
            text = extract_text(v)
            if text:
                values.append(text)

        return " ".join(values)

    return str(content)
