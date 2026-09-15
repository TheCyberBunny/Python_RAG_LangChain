"""
/analytics routes.
"""

from fastapi import APIRouter, Depends

from app.api.deps import KnowledgeBaseService, get_knowledge_base_service
from app.api.schemas import WorkloadReport, DocumentOwnershipReport
from app.api.security import require_api_key

# Same pattern as documents.py and tickets.py: dependencies=[Depends(require_api_key)]
# protects every route on this router and makes it show up correctly
# in the OpenAPI schema / Swagger UI's Authorize flow.
router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
    dependencies=[Depends(require_api_key)],
)


@router.get("/workload", response_model=WorkloadReport)
def get_team_workload(
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> WorkloadReport:
    # compute_team_workload() returns a plain dict shaped to match
    # WorkloadReport exactly - unpacked with **, the same construction
    # style MismatchOut uses, just for a whole nested report instead
    # of one flat object.
    report = service.get_team_workload_report()
    return WorkloadReport(**report)


@router.get("/document-ownership", response_model=DocumentOwnershipReport)
def get_document_ownership(
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> DocumentOwnershipReport:
    report = service.get_document_ownership_report()
    return DocumentOwnershipReport(**report)