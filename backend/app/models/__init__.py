"""
Package init - lets us write:
    from app.models import Document, Ticket
instead of:
    from app.models.document import Document
    from app.models.ticket import Ticket
"""

# The leading dot means "import from this same package" - a relative
# import. `.enums` refers to enums.py sitting right next to this file.
from .enums import DocumentCategory, TicketPriority, TicketStatus
from .document import Document
from .ticket import Ticket
from .comment import Comment
from .user import User

# __all__ declares this package's public surface - similar in spirit to
# choosing what's public vs. package-private in Java, though Python
# only enforces this for `from app.models import *`, nothing more.
__all__ = [
    "DocumentCategory", "TicketPriority", "TicketStatus",
    "Document", "Ticket", "Comment", "User",
]