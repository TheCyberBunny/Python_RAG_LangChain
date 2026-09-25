"""
The second half of RAG: takes a retriever's output and actually
answers the question with it, grounded in the retrieved context, with
citations back to the documents that context came from.

Everything up through yesterday only ever returned documents. This
module is the first thing in app/rag/ that calls an LLM - that's a
deliberate, meaningful line to cross, not an oversight: every function
here that touches the vector store still goes through
get_similarity_retriever() or get_threshold_retriever(), never
build_vector_store() or load_vector_store() directly, same
persistence discipline every prior module in this package follows.
"""

from __future__ import annotations

from dataclasses import dataclass

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from dataclasses import dataclass, field

from langchain_core.documents import Document as LCDocument
from langchain_core.output_parsers import StrOutputParser

from langchain_ollama import ChatOllama

from app.rag.retriever import (
    DEFAULT_K,
    format_retrieved_context,
    get_similarity_retriever,
    get_threshold_retriever
)

# A second, dedicated ChatOllama instance - not a reuse of
# app.ai.chains's own module-private _llm. temperature=0.0 here,
# deliberately lower than that module's 0.2: grounded Q&A wants the
# model reproducing what the retrieved context actually says, not
# adding conversational variety on top of it.
_llm = ChatOllama(
    model="llama3.2",
    base_url="http://localhost:11434",
    temperature=0.0,
)

_rag_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are DevMate, an internal engineering assistant for "
        "Northbeam. Answer the engineer's question using ONLY the "
        "context below - do not use any outside knowledge, and do not "
        "invent details that aren't in the context. If the context "
        "doesn't contain enough information to answer the question, "
        "say so plainly instead of guessing.\n\nContext:\n{context}",
    ),
    ("human", "{question}"),
])

# The same linear prompt | llm | output-parser shape every chain in
# app/ai/chains.py already uses - nothing about answering a grounded
# question needs a different composition style, just a different
# prompt and a fresh retrieved context every call.
rag_answer_chain = _rag_prompt | _llm | StrOutputParser()


@dataclass
class AskResult:
    """
    What answer_question() and answer_question_strict() both return -
    the API layer turns this into an AskResponse, but this class
    itself knows nothing about FastAPI or Pydantic.
    """
    answer: str
    sources: list[str]


def _citation_titles(documents: list[LCDocument]) -> list[str]:
    """
    Document titles, in first-seen order, with duplicates dropped.
    Today's corpus never returns two chunks from the same document,
    but a larger corpus eventually will, and a citation list is more
    useful to an engineer without the same source listed three times.
    """
    seen: set[str] = set()
    titles: list[str] = []
    for document in documents:
        title = document.metadata["title"]
        if title not in seen:
            seen.add(title)
            titles.append(title)
    return titles


def answer_question(question: str, k: int = DEFAULT_K) -> AskResult:
    """
    The full RAG path: retrieve, format, generate, cite. Always calls
    the LLM, even if the retrieved context turns out to be a weak
    match - get_similarity_retriever always returns k results
    regardless of quality, exactly as covered yesterday.
    """
    retriever = get_similarity_retriever(k=k)
    documents = retriever.invoke(question)
    context = format_retrieved_context(documents)
    answer = rag_answer_chain.invoke({"context": context, "question": question})
    return AskResult(answer=answer, sources=_citation_titles(documents))


NOT_CONFIDENT_ANSWER = (
    "I don't have enough confidence in Northbeam's documents to answer "
    "that question. Try rephrasing it, or check with the relevant team "
    "directly."
)


def answer_question_strict(
    question: str, score_threshold: float, k: int = DEFAULT_K
) -> AskResult:
    """
    Same shape as answer_question, but uses yesterday's
    get_threshold_retriever instead of get_similarity_retriever. When
    nothing in the corpus clears score_threshold, this returns a fixed,
    honest "not confident enough" answer with an empty sources list -
    WITHOUT ever calling the LLM. Calling the LLM with an empty or
    near-empty context risks it answering from outside knowledge
    despite the prompt's instructions not to - the cheapest, most
    reliable way to prevent that specific failure mode is to never
    make the call in the first place.
    """
    retriever = get_threshold_retriever(score_threshold=score_threshold, k=k)
    documents = retriever.invoke(question)

    if not documents:
        return AskResult(answer=NOT_CONFIDENT_ANSWER, sources=[])

    context = format_retrieved_context(documents)
    answer = rag_answer_chain.invoke({"context": context, "question": question})
    return AskResult(answer=answer, sources=_citation_titles(documents))

# --- Everything below is new: a formal, composed retrieval_chain, and
# conversation memory built on top of it. answer_question and
# answer_question_strict above are untouched - both keep working
# exactly as they did before, unaffected by anything that follows. ---

# A second prompt, deliberately separate from _rag_prompt above rather
# than a mutation of it: this one adds a running summary and a
# MessagesPlaceholder for the conversation's most recent raw turns.
# Reusing _rag_prompt and just adding these two inputs to it would
# break answer_question and answer_question_strict, both of which
# still call rag_answer_chain with only {context, question} - neither
# of them owns or wants conversation state.
_rag_prompt_with_history = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are DevMate, an internal engineering assistant for "
        "Northbeam. Answer the engineer's question using ONLY the "
        "context below - do not use any outside knowledge, and do not "
        "invent details that aren't in the context. If the context "
        "doesn't contain enough information to answer the question, "
        "say so plainly instead of guessing.\n\nContext:\n{context}\n\n"
        "Summary of the conversation so far (empty if this is the "
        "first question): {summary}",
    ),
    MessagesPlaceholder("recent_turns"),
    ("human", "{question}"),
])

rag_answer_chain_with_history = _rag_prompt_with_history | _llm | StrOutputParser()

def _retrieve(input_dict: dict) -> list[LCDocument]:
    """
    Rebuilds the retriever fresh on every call via get_similarity_retriever
    - never a retriever captured once and reused - the same persistence
    discipline every retrieval function in this project has followed
    since load_vector_store() was first written. Takes the whole
    accumulated dict rather than a bare question string because that's
    what RunnablePassthrough.assign(...) below hands every step.
    """
    retriever = get_similarity_retriever(k=DEFAULT_K)
    return retriever.invoke(input_dict["question"])


# The formal retrieval_chain: one composed Runnable replacing what
# answer_question does as three separately-invoked plain Python
# statements. RunnablePassthrough.assign(...) merges a new key into
# the existing input dict on each step - documents, then context, then
# answer - so every later step can see everything every earlier step
# already produced. Each value passed to assign(...) here is a plain
# Python callable or an existing Runnable; none of them needed an
# explicit RunnableLambda(...) wrapper, because assign(...) coerces a
# plain callable automatically.
retrieval_chain = (
    RunnablePassthrough.assign(documents=_retrieve)
    | RunnablePassthrough.assign(context=lambda x: format_retrieved_context(x["documents"]))
    | RunnablePassthrough.assign(answer=rag_answer_chain_with_history)
)

@dataclass
class ConversationMemory:
    """
    Caller-owned conversation state - the same ownership model
    ask_ticket_followup and ask_document_followup already established
    earlier this week (the CALLER holds the history and passes it in
    every call), just with a running summary added on top of the raw
    message list. Nothing here talks to a database, a file, or
    survives a process restart.
    """
    summary: str = ""
    recent_messages: list[BaseMessage] = field(default_factory=list)


# Kept deliberately small so the summarization path in record_turn()
# below is easy to exercise and observe - two full question/answer
# turns (4 messages) stay in raw form; anything older gets folded into
# summary two turns at a time.
MAX_RECENT_MESSAGES = 4

_summary_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "Summarize the conversation turns below in 2-3 sentences, "
        "preserving anything factual an engineer would need to answer "
        "a follow-up question. If an existing summary is given, build "
        "on it rather than starting over from nothing. Write only the "
        "summary itself - do not mention whether a summary already "
        "existed or comment on these instructions.\n\n"
        "Existing summary (empty if there isn't one yet): {existing_summary}",
    ),
    MessagesPlaceholder("turns_to_summarize"),
    ("human", "Summarize the conversation above, following the instructions given."),
])

# The same _llm this module already uses for grounded answering, not a
# third ChatOllama instance - summarizing faithfully is the same kind
# of low-variance, low-creativity task grounded answering already is.
summarization_chain = _summary_prompt | _llm | StrOutputParser()


def record_turn(memory: ConversationMemory, question: str, answer: str) -> None:
    """
    Appends this turn's messages to memory.recent_messages, then folds
    the oldest overflow into memory.summary once more than
    MAX_RECENT_MESSAGES have accumulated. Mutates memory in place -
    callers keep the same ConversationMemory instance across turns.
    """
    memory.recent_messages.append(HumanMessage(content=question))
    memory.recent_messages.append(AIMessage(content=answer))

    if len(memory.recent_messages) > MAX_RECENT_MESSAGES:
        overflow = memory.recent_messages[:-MAX_RECENT_MESSAGES]
        memory.recent_messages = memory.recent_messages[-MAX_RECENT_MESSAGES:]
        raw_summary = summarization_chain.invoke({
            "existing_summary": memory.summary,
            "turns_to_summarize": overflow,
        })
        print(f"[DEBUG] existing_summary going in: {memory.summary!r}")
        print(f"[DEBUG] raw summarization_chain output: {raw_summary!r}")
        memory.summary = raw_summary
        

def ask_with_memory(memory: ConversationMemory, question: str) -> AskResult:
    """
    The memory-aware sibling of answer_question: runs retrieval_chain
    with this conversation's summary and recent raw turns folded into
    the prompt, then records the new turn - updating memory.summary if
    that push crosses MAX_RECENT_MESSAGES - before returning.
    """
    result = retrieval_chain.invoke({
        "question": question,
        "summary": memory.summary,
        "recent_turns": memory.recent_messages,
    })
    record_turn(memory, question, result["answer"])
    return AskResult(answer=result["answer"], sources=_citation_titles(result["documents"]))

# In-process, in-memory only - lost on every restart, and shared with
# no locking across every request the running process handles for a
# given id. Both real, worth-knowing limitations, not oversights being
# silently worked around here.
_conversations: dict[str, ConversationMemory] = {}


def get_conversation_memory(conversation_id: str) -> ConversationMemory:
    """
    Returns the existing ConversationMemory for this id, creating a
    new one on first use. The API layer's conversation route is the
    only caller - scripts/day11_demo.py manages its own
    ConversationMemory directly, with no id involved at all.
    """
    if conversation_id not in _conversations:
        _conversations[conversation_id] = ConversationMemory()
    return _conversations[conversation_id]
