"""
LangChain fundamentals: one prompt-template-and-chain pattern, reused
for Ticket summaries today (Phase A) and Document descriptions in the
challenge (Phase B).

Nothing in this module talks to FastAPI, KnowledgeBaseService, or any
other part of the app - same separation of concerns
app/analytics/workload.py already established: a focused module that
knows how to do ONE thing (turn a Ticket or Document into a plain-
English sentence via a local LLM), with no awareness of whatever
calls it.
"""

from __future__ import annotations

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

# One shared ChatOllama instance for this whole module - every chain
# below reuses it rather than constructing its own. base_url is
# spelled out explicitly even though it matches Ollama's own default,
# so it's obvious at a glance where this is actually talking to.
_llm = ChatOllama(
    model="llama3.2",
    base_url="http://localhost:11434",
    temperature=0.2,
)


"""
chatprompttemplate formats a list of messages - in this instance, a system message
setting the model's role and rules, and a human message carrying the actual request.
title, priority, and status are placeholders that get filled further down the chain
"""
_ticket_summary_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are DevMate, an internal engineering assistant for "
        "Northbeam. Summarize the given ticket in exactly one plain "
        "English sentence, written for an engineer skimming a long "
        "list. Do not invent details that aren't provided.",
    ),
    (
        "human",
        "Title: {title}\nPriority: {priority}\nStatus: {status}",
    ),
])

# The whole point of LCEL(lang chain expression language): three independent, 
# swappable pieces - a prompt template, a chat model, an output parser - composed
# with `|` into one callable pipeline. Swapping _llm for a different provider
# later means changing this one shared instance, not every chain.
ticket_summary_chain = _ticket_summary_prompt | _llm | StrOutputParser()


def summarize_ticket(title: str, priority: str, status: str) -> str:
    """Thin, testable wrapper - the actual entry point other code calls."""
    return ticket_summary_chain.invoke({
        "title": title,
        "priority": priority,
        "status": status,
    })


_document_description_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are DevMate, an internal engineering assistant for "
        "Northbeam. Write exactly one plain English sentence "
        "describing the given document - what it covers, and whether "
        "it looks due for review given how long it's been since its "
        "last review. Do not invent details that aren't provided.",
    ),
    (
        "human",
        "Title: {title}\nCategory: {category}\n"
        "Days since last reviewed: {days_since_reviewed}",
    ),
])

# Same shared _llm as ticket_summary_chain above - one ChatOllama
# instance for the whole module, not a second one constructed here.
document_description_chain = _document_description_prompt | _llm | StrOutputParser()


def describe_document(title: str, category: str, days_since_reviewed: int) -> str:
    """Thin, testable wrapper - mirrors summarize_ticket's exact shape."""
    return document_description_chain.invoke({
        "title": title,
        "category": category,
        "days_since_reviewed": days_since_reviewed,
    })