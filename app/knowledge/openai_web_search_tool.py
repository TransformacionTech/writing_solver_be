from crewai.tools import BaseTool
from openai import OpenAI

from app.core.config import settings

_client = OpenAI(api_key=settings.openai_api_key)


class OpenAIWebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = (
        "Search the web for recent information about a topic. "
        "Input: a search query string. "
        "Output: relevant information found on the web."
    )

    def _run(self, search_query: str) -> str:
        response = _client.responses.create(
            model="gpt-4o-mini",
            tools=[{"type": "web_search_preview"}],
            input=search_query,
        )
        return response.output_text


openai_web_search = OpenAIWebSearchTool()
