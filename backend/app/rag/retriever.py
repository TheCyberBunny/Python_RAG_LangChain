"""
Wraps the already-persisted Chroma vector store as a LangChain
retriever, and formats retrieved chunks into a citation-ready context
string - the last piece standing between "a store that can be
searched" and "an LLM call that can answer a question grounded in
what it found."

Nothing here calls an LLM, and nothing here builds or rebuilds the
vector store - same persistence discipline search_documents already
established. That's exactly why every function below reads from
load_vector_store(), never build_vector_store().
"""

from __future__ import annotations

from langchain_core.documents import Document as LCDocument

from app.rag.vector_store import load_vector_store

#this constant is used to set the default # of results from the retriever
DEFAULT_K = 4


def get_similarity_retriever(k: int = DEFAULT_K, category: str | None = None):
    """
    Plain nearest-neighbor retrieval - the default search_type, ranked
    purely by closeness to the query. Mirrors search_documents's own
    category-filtering rule: the filter argument is only added when a
    category is actually given, never passed as {"category": None}.
    """
    #first, we load our vector database store
    vector_store = load_vector_store()
    #next, we set up the search parameters, specifically the # of results to return
    search_kwargs: dict = {"k": k}
    if category is not None:
        #if a category is provided, we add it to the search params as a filter
        search_kwargs["filter"] = {"category": category}
    return vector_store.as_retriever(search_type="similarity", search_kwargs=search_kwargs)

def get_diverse_retriever(k: int = DEFAULT_K, fetch_k: int = 20, lambda_mult: float = 0.5):
    """
    MMR (Maximal Marginal Relevance) retrieval - pulls `fetch_k`
    similarity candidates first, then re-ranks them to balance
    relevance against diversity, so results aren't all near-duplicates
    of the same underlying idea. lambda_mult=1.0 behaves like plain
    similarity search (minimum diversity); lower values favor
    diversity more, down to 0.0 (maximum diversity).
    """
    vector_store = load_vector_store()
    return vector_store.as_retriever(
        search_type="mmr",
        search_kwargs={"k": k, "fetch_k": fetch_k, "lambda_mult": lambda_mult},
    )

def format_retrieved_context(documents: list[LCDocument]) -> str:
    """
    Turns retrieved chunks into a single citation-ready string, e.g.:

        [Source: Incident Response Runbook]
        Steps to triage a P1 incident: ...

    This is exactly the shape a prompt needs to hand grounded context
    to an LLM alongside a question - built today, used tomorrow.
    """
    return "\n\n".join(
        f"[Source: {document.metadata['title']}]\n{document.page_content}"
        for document in documents
    )

def get_threshold_retriever(score_threshold: float, k: int = DEFAULT_K):
    """
    Returns fewer than k results - including zero - when nothing in
    the corpus clears score_threshold, rather than always returning
    exactly k regardless of how weak the worst match is. Uses
    load_vector_store(), never build_vector_store(), same persistence
    discipline every other function in this file follows.
    """
    vector_store = load_vector_store()
    return vector_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"score_threshold": score_threshold, "k": k},
    )