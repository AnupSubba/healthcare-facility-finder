"""Explain terms (NABH, NABL, PM-JAY...) using only the glossary knowledge cards (RAG)."""

from functools import lru_cache

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from .. import config
from .llm import chat_model

PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You explain healthcare terms to ordinary people in India in simple words. Use ONLY the context. "
            "Answer in under 120 words. Never give medical advice. If the context doesn't cover the question, "
            "say you don't have information on it. Answer in {language_name}.",
        ),
        ("human", "Question: {question}\n\nContext:\n{context}"),
    ]
)


class GlossaryMissingError(RuntimeError):
    pass


@lru_cache
def _retriever():
    if not config.CHROMA_DIR.exists():
        raise GlossaryMissingError("Glossary index not found. Run: uv run python scripts/ingest_glossary.py")
    from langchain_chroma import Chroma
    from langchain_community.embeddings import FastEmbedEmbeddings

    store = Chroma(
        persist_directory=str(config.CHROMA_DIR),
        collection_name=config.COLLECTION,
        embedding_function=FastEmbedEmbeddings(model_name=config.EMBED_MODEL),
    )
    return store.as_retriever(search_kwargs={"k": 3})


def explain_term(question: str, language: str = "en") -> tuple[str, list[str]]:
    docs = _retriever().invoke(question)
    context = "\n\n".join(f"[{d.metadata.get('url', '')}]\n{d.page_content}" for d in docs)
    chain = PROMPT | chat_model() | StrOutputParser()
    answer = chain.invoke(
        {"question": question, "context": context, "language_name": "Hindi" if language == "hi" else "English"}
    )
    sources = list(dict.fromkeys(d.metadata["url"] for d in docs if d.metadata.get("url")))
    return answer.strip(), sources
