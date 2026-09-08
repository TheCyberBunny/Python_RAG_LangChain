"""
Document model - Day 1 plain-Python version.
No database yet: state lives only in the `registry` class attribute.
"""

from datetime import date
from typing import ClassVar  # lets us type-hint a class-level (shared) attribute

from .enums import DocumentCategory


class Document:
    # Class attributes - declared here, OUTSIDE __init__ - are shared
    # by every Document instance. This is the Python equivalent of a
    # `static` field in Java: there is only ONE `registry` list, and
    # every Document ever created gets appended to that same list.
    registry: ClassVar[list["Document"]] = []
    STALE_THRESHOLD_DAYS: ClassVar[int] = 90

    #methods with leading and trailing double underscores are called 'Dunder' methods
    def __init__(self, document_id: int, title: str, category: DocumentCategory,
                 body: str, owner_id: int, last_reviewed_at: date | None = None):
        # `self` is explicit in Python - it IS the object being built,
        # equivalent to the implicit `this` inside a Java constructor.
        self.id = document_id
        self.title = title
        self.category = category
        self.body = body
        self.owner_id = owner_id
        # `x or y` returns x if x is "truthy", otherwise y. None is
        # falsy, so: no last_reviewed_at passed in -> use today's date.
        self.last_reviewed_at = last_reviewed_at or date.today()
        Document.registry.append(self)  # register this instance globally

    def days_since_reviewed(self, as_of: date | None = None) -> int:
        today = as_of or date.today()
        # Subtracting two `date` objects gives a `timedelta`; `.days`
        # pulls the whole-number day count out of it.
        return (today - self.last_reviewed_at).days

    def is_stale(self, threshold: int | None = None, as_of: date | None = None) -> bool:
        # NOTE: this is `threshold if threshold is not None else ...`,
        # not `threshold or Document.STALE_THRESHOLD_DAYS`. If a caller
        # ever passed threshold=0, `0 or DEFAULT` would incorrectly
        # fall back to DEFAULT, because 0 is falsy. Checking `is not
        # None` explicitly avoids that trap.
        limit = threshold if threshold is not None else Document.STALE_THRESHOLD_DAYS
        return self.days_since_reviewed(as_of) > limit

    @classmethod  # receives the CLASS itself as `cls`, not an instance
    def find_by_id(cls, document_id: int) -> "Document | None":
        for document in cls.registry:
            if document.id == document_id:
                return document
        return None  # no match found

    def __repr__(self) -> str:
        # __repr__ controls what shows up when you `print()` an object
        # or inspect it in a debugger - similar in spirit to overriding
        # toString() in Java.
        return (f"Document(id={self.id}, title={self.title!r}, "
                f"category={self.category.value}, "
                f"last_reviewed_at={self.last_reviewed_at.isoformat()})")