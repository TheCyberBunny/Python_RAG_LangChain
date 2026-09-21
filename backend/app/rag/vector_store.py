"""
Chunking, embedding, and storing DevMate's Document corpus in a local
Chroma vector store - the groundwork retrieval needs before a real
question can be answered against it.

Nothing in this module talks to FastAPI, KnowledgeBaseService, or any
other part of the app - same separation of concerns app/ai/chains.py
already established: a focused module that knows how to do ONE thing
(turn Document rows into a searchable vector store), with no awareness
of whatever calls it.
"""

from __future__ import annotations

from langchain_chroma import Chroma
from langchain_core.documents import Document as LCDocument
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.models import Document

# 500/50 is a reasonable general-purpose starting point for chunk
# size/overlap - generous enough that this project's own short
# document bodies won't actually get split at all (every one of them
# is under 150 characters), while still being a realistic setting for
# a document corpus that grows past a single paragraph later.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
EMBEDDING_MODEL = "nomic-embed-text"
PERSIST_DIRECTORY = "chroma_db"

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
)

# Same shared-instance habit ai/chains.py established for _llm - one
# OllamaEmbeddings instance for this whole module.
_embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)


def _document_to_metadata(document: Document) -> dict:
    """
    Chroma's underlying client only accepts str/int/float/bool metadata
    values - no None, no nested dicts or lists. last_reviewed_at is a
    plain Python date object on our Document model, so it has to be
    converted to a string here, or the write to Chroma fails outright
    later with a confusing error that has nothing to do with dates on
    its surface.
    """
    return {
        "document_id": document.id,
        "title": document.title,
        "category": document.category.value,
        "last_reviewed_at": document.last_reviewed_at.isoformat(),
    }


def documents_to_chunks(documents: list[Document]) -> list[LCDocument]:
    """
    Turns our own Document objects into LangChain's Document objects,
    then splits them into chunks. Two different classes that happen to
    share a name - kept straight here only by the `LCDocument` import
    alias, since nothing about the name itself distinguishes them.
    """
    lc_documents = [
        LCDocument(page_content=document.body, metadata=_document_to_metadata(document))
        for document in documents
    ]
    return _splitter.split_documents(lc_documents)


def build_vector_store(
    documents: list[Document], persist_directory: str = PERSIST_DIRECTORY
) -> Chroma:
    """
    Chunks, embeds, and persists the given documents to a fresh (or
    appended-to) Chroma collection on disk. No separate .persist()
    call - passing persist_directory here is enough; writes land on
    disk as they happen.
    """
    chunks = documents_to_chunks(documents)
    return Chroma.from_documents(
        documents=chunks,
        embedding=_embeddings,
        persist_directory=persist_directory,
    )


def load_vector_store(persist_directory: str = PERSIST_DIRECTORY) -> Chroma:
    """
    Reopens an already-persisted Chroma collection without re-chunking
    or re-embedding anything - the point of persistence in the first
    place. `embedding_function` (not `embedding`) is the constructor's
    parameter name for this specific path.
    """
    return Chroma(
        persist_directory=persist_directory,
        embedding_function=_embeddings,
    )

def search_documents(
    query: str, k: int = 3, category: str | None = None
) -> list[LCDocument]:
    """
    Searches the already-persisted collection - never rebuilds it.
    Uses load_vector_store(), not build_vector_store(), so this works
    correctly even called from a process that never ran the ingestion
    step itself, the way a real application would query a store
    populated once, potentially hours or days earlier.
    """
    vector_store = load_vector_store()
    if category is not None:
        return vector_store.similarity_search(query, k=k, filter={"category": category})
    return vector_store.similarity_search(query, k=k)