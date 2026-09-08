"""
User model - Day 1 Answer Key (Phase B / Business Question #2).

Not part of Phase A's explicit entity list, but implied by
Document.owner_id, Ticket.assignee_id, and Comment.author_id. Follows
the exact same registry/find_by_id pattern established by Document,
Ticket, and Comment.
"""

from typing import ClassVar


class User:
    registry: ClassVar[list["User"]] = []

    def __init__(self, user_id: int, name: str, team: str):
        self.id = user_id
        self.name = name
        self.team = team
        User.registry.append(self)

    @classmethod
    def find_by_id(cls, user_id: int) -> "User | None":
        for user in cls.registry:
            if user.id == user_id:
                return user
        return None

    def __repr__(self) -> str:
        return f"User(id={self.id}, name={self.name!r}, team={self.team!r})"