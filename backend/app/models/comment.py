"""
Comment model - Day 1 plain-Python version.
Attaches to exactly one Ticket - the same one-to-many shape every later
"log entry" style model in this codebase will follow.
"""

from datetime import datetime
from typing import ClassVar


class Comment:
    registry: ClassVar[list["Comment"]] = []

    def __init__(self, comment_id: int, ticket_id: int, author_id: int,
                 body: str, created_at: datetime | None = None):
        self.id = comment_id
        self.ticket_id = ticket_id  # which Ticket this comment belongs to
        self.author_id = author_id  # which User wrote it (User doesn't exist until Phase B)
        self.body = body
        # IMPORTANT PYTHON GOTCHA: writing
        #     created_at: datetime = datetime.now()
        # as the default would be evaluated ONCE, the moment Python
        # first reads this class - every Comment created without an
        # explicit timestamp would then share that exact same frozen
        # moment. Defaulting to None and calling datetime.now() here,
        # inside the method body, means it re-evaluates fresh every
        # single time a new Comment is actually created.
        self.created_at = created_at or datetime.now()
        Comment.registry.append(self)

    def __repr__(self) -> str:
        return (f"Comment(id={self.id}, ticket_id={self.ticket_id}, "
                f"author_id={self.author_id})")