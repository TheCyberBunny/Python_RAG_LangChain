"""
/tickets routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.api.deps import KnowledgeBaseService, get_knowledge_base_service
from app.api.schemas import MismatchOut, TicketOut, TicketPage
from app.api.security import require_api_key

# Same pattern as documents.py: dependencies=[Depends(require_api_key)]
# protects every route on this router and makes it show up correctly
# in the OpenAPI schema / Swagger UI's Authorize flow.
router = APIRouter(
    prefix="/tickets",
    tags=["tickets"],
    dependencies=[Depends(require_api_key)],
)


@router.get("", response_model=TicketPage, status_code=status.HTTP_200_OK)
def list_tickets(
    skip: int = Query(0, ge=0, description="Number of tickets to skip"),
    limit: int = Query(10, ge=1, le=100, description="Max tickets to return"),
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> TicketPage:
    # Identical shape to documents.py's list_documents - the same
    # envelope pattern (items/total/skip/limit), the same reason for
    # it (total reflects the FULL set so a client knows when to stop
    # paging), just applied to a different collection.
    all_tickets = service.get_all_tickets()
    page = all_tickets[skip: skip + limit]
    return TicketPage(
        items=[TicketOut.model_validate(ticket) for ticket in page],
        total=len(all_tickets),
        skip=skip,
        limit=limit,
    )


@router.get("/mismatches", response_model=list[MismatchOut])
def list_team_mismatches(
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> list[MismatchOut]:
    # Business Question #2, as an HTTP endpoint. Each mismatch is a
    # 4-tuple (ticket, document, assignee, owner) - MismatchOut is
    # built by hand from those four objects, the same way
    # StaleDocumentOut was built from a single Document plus a
    # computed value.
    return [
        MismatchOut(
            ticket_id=ticket.id,
            ticket_title=ticket.title,
            assignee_name=assignee.name,
            assignee_team=assignee.team,
            owner_name=owner.name,
            owner_team=owner.team,
        )
        for ticket, document, assignee, owner in service.get_team_mismatches()
    ]

# IMPORTANT: this route MUST be declared after "/mismatches" above, not
# before it - the exact same route-ordering gotcha from documents.py.
# "/{ticket_id}" structurally matches any single path segment,
# including the literal text "mismatches" - if this were declared
# first, GET /tickets/mismatches would be routed HERE instead, and
# fail with a 422 the moment FastAPI tries to convert "mismatches"
# into an int.
@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(
    ticket_id: int,
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> TicketOut:
    ticket = service.get_ticket_by_id(ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No ticket with id {ticket_id}",
        )
    return TicketOut.model_validate(ticket)