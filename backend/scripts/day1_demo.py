"""
Day 1 demo script - DevMate, Northbeam's internal engineering assistant
Run from backend/ with the venv active:
    python -m scripts.day1_demo
"""

from datetime import date, timedelta

from app.models import Document, Ticket, Comment, User
from app.models import DocumentCategory, TicketPriority


def find_stale_documents(documents: list[Document], threshold: int = 90) -> list[Document]:
    """
    Business Question #1: Stale Documentation Report
    Which non-Postmortem documents haven't been reviewed in over
    `threshold` days?
    """
    # List comprehension: builds a new list by keeping only the
    # `document` values where the condition after `if` is True.
    # Roughly equivalent to a Java Stream's .filter(...).collect(...),
    # or a plain for-loop with an `if` and a manual .append() call:
    #
    #   result = []
    #   for document in documents:
    #       if document.category != DocumentCategory.POSTMORTEM and document.is_stale(threshold):
    #           result.append(document)
    #   return result
    return [
        document for document in documents
        if document.category != DocumentCategory.POSTMORTEM
        and document.is_stale(threshold)
    ]

def find_team_mismatches(
    tickets: list[Ticket],
    documents: list[Document],
    users: list[User],
) -> list[tuple[Ticket, Document, User, User]]:
    """
    Business Question #2: Team Mismatch Report
    Which tickets are assigned to a user whose team does NOT match the
    team of the user who owns the ticket's related document?

    Takes tickets/documents/users as parameters rather than reaching
    into Ticket.registry / Document.registry / User.registry directly,
    so the function stays testable against any data set, not just
    whatever's been seeded at import time.
    """
    mismatches: list[tuple[Ticket, Document, User, User]] = []

    for ticket in tickets:
        if ticket.related_document_id is None:
            continue

        document = Document.find_by_id(ticket.related_document_id)
        assignee = User.find_by_id(ticket.assignee_id)

        # Defensive guard: a ticket referencing a document_id or
        # assignee_id that doesn't exist in the registry isn't a team
        # mismatch - it's a data integrity problem. Skip it here; a
        # later validation layer handles that properly.
        if document is None or assignee is None:
            continue

        owner = User.find_by_id(document.owner_id)
        if owner is None:
            continue

        if assignee.team != owner.team:
            mismatches.append((ticket, document, assignee, owner))

    return mismatches


def seed_demo_data() -> None:
    today = date.today()

    # Positional args first (document_id, title, category), then
    # keyword args (body=..., owner_id=..., last_reviewed_at=...).
    # Once you use ONE keyword argument, every argument after it must
    # also be passed by keyword - Python enforces this at import time.
    Document(1, "Incident Response Runbook", DocumentCategory.RUNBOOK,
             body="Steps to triage a P1 incident...", owner_id=301,
             last_reviewed_at=today - timedelta(days=120))  # timedelta = "N days" as a subtractable amount
    Document(2, "Onboarding: Local Dev Setup", DocumentCategory.ONBOARDING,
             body="Clone the repo, run make setup...", owner_id=302,
             last_reviewed_at=today - timedelta(days=10))
    Document(3, "Q2 Outage Postmortem", DocumentCategory.POSTMORTEM,
             body="On May 3rd, the auth service...", owner_id=301,
             last_reviewed_at=today - timedelta(days=200))
    Document(4, "Deploy Pipeline Wiki", DocumentCategory.WIKI,
             body="Our CI/CD pipeline runs in three stages...", owner_id=303,
             last_reviewed_at=today - timedelta(days=95))

     # User 301 owns Document 1 (SRE) and Document 3.
    # User 302 is on Platform, but is about to be assigned a ticket tied
    # to an SRE-owned document below - a deliberate team mismatch.
    # User 304 is on SRE, same team as Document 4's owner (303) - no
    # mismatch, even though 304 and 303 are different people.
    User(301, "A. Kim", team="SRE")
    User(302, "B. Osei", team="Platform")
    User(303, "C. Diaz", team="SRE")
    User(304, "D. Farah", team="SRE")

    Ticket(1, "Runbook missing rollback step", TicketPriority.HIGH,
           assignee_id=302, related_document_id=1)
    Ticket(2, "Wiki page has broken links", TicketPriority.LOW,
           assignee_id=303, related_document_id=4)

    Comment(1, ticket_id=1, author_id=301,
            body="Confirmed - step 4 references a script that no longer exists.")


def main() -> None:
    seed_demo_data()  # populate the in-memory registries with sample data

    print("== Full Document Registry ==")
    for document in Document.registry:
        # print(document) calls Document.__repr__ automatically - this
        # loop is where that method's return value actually shows up.
        print(document)

    print("\n== Stale Documentation Report (> 90 days) ==")
    stale = find_stale_documents(Document.registry, threshold=90)
    if not stale:
        print("  No stale documents.")
    for document in stale:
        # f-string: the {expression} parts are evaluated and inserted
        # directly into the string. The `!r` conversion calls repr()
        # on the value instead of str() - here, that wraps the title
        # in quotes so it stands out visually from the rest of the line.
        print(f"  STALE: {document.title!r} last reviewed "
              f"{document.days_since_reviewed()} days ago "
              f"({document.category.value})")

    print("\n== Team Mismatch Report ==")
    mismatches = find_team_mismatches(Ticket.registry, Document.registry, User.registry)
    if not mismatches:
        print("  No mismatches found.")
    for ticket, document, assignee, owner in mismatches:
        print(f"  Ticket {ticket.id} ({ticket.title!r}): "
              f"assignee {assignee.name} ({assignee.team}), "
              f"doc owner {owner.name} ({owner.team})")    


if __name__ == "__main__":
    # This block only runs when the file is EXECUTED directly, e.g.
    # `python -m scripts.day1_demo`. Python sets the special __name__
    # variable to "__main__" only in the file you actually ran - any
    # other file that IMPORTS this one instead sees __name__ equal to
    # this module's own name, so main() won't fire just by importing it.
    main()