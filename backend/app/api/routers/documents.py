"""
/documents routes.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import KnowledgeBaseService, get_knowledge_base_service
from app.api.schemas import DocumentOut, StaleDocumentOut, DocumentPage
from app.api.security import require_api_key

# dependencies=[Depends(require_api_key)] applies to EVERY route on
# this router - each one now requires a valid X-API-Key, and each one
# shows up in the OpenAPI schema (and therefore Swagger UI) as requiring
# it, without repeating the dependency on every single route function.
router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    dependencies=[Depends(require_api_key)],
)

# the response model tells FastAPI to validate the value against the schema
#the status code tells FastAPI to return a 200 OK instead of the default 422 Unprocessable Entity if the response model validation fails
@router.get("", response_model=DocumentPage, status_code=status.HTTP_200_OK)
def list_documents(
    #Here, Query() is used to declare query parameters for the endpoint. Skip and limit are optional
    #parameters to control pagination. ge and le stands for greater than or equal and less than or equal
    skip: int = Query(0, ge=0, description="Number of documents to skip"),
    limit: int = Query(10, ge=1, le=100, description="Max documents to return"),
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> DocumentPage:
    all_documents = service.get_all_documents()
    page = all_documents[skip: skip + limit]
    return DocumentPage(
        items=[DocumentOut.model_validate(document) for document in page],
        total=len(all_documents),
        skip=skip,
        limit=limit,
    )


@router.get("/stale", response_model=list[StaleDocumentOut])
def list_stale_documents(
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> list[StaleDocumentOut]:
    # Business Question #1, as an HTTP endpoint. StaleDocumentOut needs
    # days_since_reviewed, which is a METHOD CALL, not a plain
    # attribute - so this one is built by hand instead of going through
    # model_validate().
    return [
        StaleDocumentOut(
            id=document.id,
            title=document.title,
            category=document.category,
            days_since_reviewed=document.days_since_reviewed(),
        )
        for document in service.get_stale_documents(threshold=90)
    ]

# IMPORTANT: this route MUST be declared after "/stale" above, not
# before it. FastAPI matches routes in declaration order, and
# "/{document_id}" would structurally match the literal path "/stale"
# too (it matches any single path segment) - if this were declared
# first, a request to GET /documents/stale would be routed HERE
# instead, and fail with a 422 the moment FastAPI tries to convert the
# text "stale" into an int.
@router.get("/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: int,
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> DocumentOut:
    document = service.get_document_by_id(document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No document with id {document_id}",
        )
    return DocumentOut.model_validate(document)