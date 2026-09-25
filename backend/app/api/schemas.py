"""
Pydantic request/response schemas for the API layer.

These are deliberately separate from app.models - the plain-Python
domain classes stay exactly as they are, and these BaseModel classes
describe only what the API is willing to show a client.
"""

from datetime import date

from pydantic import BaseModel, ConfigDict

from app.models import DocumentCategory, TicketPriority, TicketStatus


class DocumentOut(BaseModel):
    # from_attributes=True (the Pydantic v2 name for the old orm_mode)
    # lets DocumentOut.model_validate(some_document) read values off a
    # plain object's ATTRIBUTES (document.id, document.title, ...)
    # instead of requiring a dict. Without this, model_validate would
    # only accept a dict, not an arbitrary Python object.
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: DocumentCategory
    owner_id: int
    last_reviewed_at: date


class StaleDocumentOut(BaseModel):
    id: int
    title: str
    category: DocumentCategory
    days_since_reviewed: int

class TicketOut(BaseModel):
    # Same from_attributes trick as DocumentOut - a Ticket's fields map
    # straight across, so no hand-built construction needed here.
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    priority: TicketPriority
    status: TicketStatus
    assignee_id: int
    related_document_id: int | None


class MismatchOut(BaseModel):
    # A mismatch isn't one object - it's a Ticket, a Document, and two
    # Users, so (like StaleDocumentOut) this one is always built by
    # hand with keyword arguments, never through model_validate().
    ticket_id: int
    ticket_title: str
    assignee_name: str
    assignee_team: str
    owner_name: str
    owner_team: str

class DocumentPage(BaseModel):
    # A pagination "envelope" - the actual page of results, plus
    # enough metadata (total, skip, limit) for a client to know
    # whether there's more to fetch, without a second request.
    items: list[DocumentOut]
    total: int
    skip: int
    limit: int

class TicketPage(BaseModel):
    items: list[TicketOut]
    total: int
    skip: int
    limit: int

class TeamWorkload(BaseModel):
    team: str
    open_ticket_count: int
    load_score: float
    load_share_pct: float
    is_overloaded: bool


class WorkloadReport(BaseModel):
    teams: list[TeamWorkload]
    total_open_tickets: int
    mean_load_score: float
    std_load_score: float

class TeamDocumentOwnership(BaseModel):
    team: str
    owned_document_count: int
    stale_document_count: int
    stale_share_pct: float
    is_stale_risk: bool


class DocumentOwnershipReport(BaseModel):
    teams: list[TeamDocumentOwnership]
    total_documents: int

class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    # Not built via model_validate() - app.rag.qa_chain.AskResult isn't
    # a domain model with from_attributes wired up, so the router
    # constructs this one field by field, the same way MismatchOut and
    # TeamWorkload already do from plain dicts/tuples elsewhere in this
    # file.
    answer: str
    sources: list[str]

class AskStrictRequest(BaseModel):
    question: str
    score_threshold: float

class AskConversationRequest(BaseModel):
    conversation_id: str
    question: str