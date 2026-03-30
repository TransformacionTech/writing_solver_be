from crewai import LLM

from app.core.config import settings

# Model assignment per agent role
AGENT_MODELS: dict[str, str] = {
    "researcher": "gpt-4o-mini",
    "writer": "gpt-5.2",
    "editor": "gpt-5.2",
    "reader": "gpt-4o-mini",
    "default": "gpt-4o-mini",
}


def _build_llm(model: str) -> LLM:
    return LLM(
        model=f"openai/{model}",
        api_key=settings.openai_api_key,
    )


# Exports consumed by agents/
llm_researcher = _build_llm(AGENT_MODELS["researcher"])
llm_writer = _build_llm(AGENT_MODELS["writer"])
llm_editor = _build_llm(AGENT_MODELS["editor"])
llm_reader = _build_llm(AGENT_MODELS["reader"])
llm_default = _build_llm(AGENT_MODELS["default"])
