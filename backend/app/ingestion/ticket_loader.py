"""
CSV-based Ticket loader - Day 2 Answer Key (Phase B).

Same shape as document_loader.py, applied to a different file format:
csv.DictReader instead of hand-rolled frontmatter parsing.
"""

import csv
from pathlib import Path

from app.core.exceptions import TicketLoadError
from app.models import Ticket, TicketPriority, TicketStatus


def _row_to_ticket(row: dict[str, str]) -> Ticket:
    try:
        priority = TicketPriority(row["priority"])
    except ValueError as exc:
        raise TicketLoadError(f"row {row.get('id')}: invalid priority {row['priority']!r}") from exc

    try:
        status = TicketStatus(row["status"])
    except ValueError as exc:
        raise TicketLoadError(f"row {row.get('id')}: invalid status {row['status']!r}") from exc

    try:
        ticket_id = int(row["id"])
        assignee_id = int(row["assignee_id"])
        # A blank related_document_id is valid (no related document) -
        # only a non-blank value that ISN'T a valid integer should raise.
        related_document_id = (
            int(row["related_document_id"]) if row["related_document_id"] else None
        )
    except ValueError as exc:
        raise TicketLoadError(
            f"row {row.get('id')}: id/assignee_id/related_document_id must be integers"
        ) from exc

    return Ticket(ticket_id, row["title"], priority, assignee_id=assignee_id,
                  related_document_id=related_document_id, status=status)


def load_tickets_from_csv(csv_path: str | Path) -> list[Ticket]:
    tickets: list[Ticket] = []

    # newline="" is required by the csv module on every platform - it
    # stops Python's own universal-newline handling from interfering
    # with the CSV format's own line-ending rules.
    with open(csv_path, newline="", encoding="utf-8") as handle:
        # DictReader turns each row into a dict keyed by the header row,
        # so row["priority"] reads far clearer than row[2] would.
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                tickets.append(_row_to_ticket(row))
            except TicketLoadError as exc:
                print(f"  SKIPPED {exc}")

    return tickets