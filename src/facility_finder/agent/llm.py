"""Chat models: Groq first, Gemini as an optional fallback."""

from functools import lru_cache

from .. import config


@lru_cache
def chat_model():
    from langchain_groq import ChatGroq

    config.require("GROQ_API_KEY")
    primary = ChatGroq(model=config.require("GROQ_MODEL"), temperature=0)
    if not config.GEMINI_MODEL:
        return primary
    from langchain_google_genai import ChatGoogleGenerativeAI

    config.require("GOOGLE_API_KEY")
    return primary.with_fallbacks([ChatGoogleGenerativeAI(model=config.GEMINI_MODEL, temperature=0)])


@lru_cache
def extractor():
    """Prompt -> LLM -> validated FacilitySearch."""
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_groq import ChatGroq

    from ..models import FacilitySearch
    from .prompts import EXTRACT_SYSTEM

    prompt = ChatPromptTemplate.from_messages([("system", EXTRACT_SYSTEM), ("human", "{question}")])
    config.require("GROQ_API_KEY")
    model = ChatGroq(model=config.require("GROQ_MODEL"), temperature=0).with_structured_output(FacilitySearch)
    if config.GEMINI_MODEL:
        from langchain_google_genai import ChatGoogleGenerativeAI

        config.require("GOOGLE_API_KEY")
        fallback = ChatGoogleGenerativeAI(model=config.GEMINI_MODEL, temperature=0).with_structured_output(
            FacilitySearch
        )
        model = model.with_fallbacks([fallback])
    return prompt | model
