from crewai.tools import BaseTool

from app.services.rag_service import query


class RagSearchTool(BaseTool):
    name: str = "rag_search"
    description: str = (
        "Search the Tech And Solve knowledge base for tone, style and format "
        "references from previously approved LinkedIn posts. "
        "Input: a short query describing what you want to find. "
        "Output: relevant text fragments from the knowledge base."
    )

    def _run(self, query_text: str) -> str:
        results = query(text=query_text, n_results=3)
        if not results:
            return "No relevant documents found in the knowledge base."
        return "\n\n---\n\n".join(results)


rag_tool = RagSearchTool()
