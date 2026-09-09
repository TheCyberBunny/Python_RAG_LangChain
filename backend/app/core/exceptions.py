"""
Custom exception hierarchy for DevMate's ingestion layer.
"""

# Custom exceptions are just classes that inherit from Exception (or
# from another exception). There's no special syntax beyond that -
# the class body below is empty because these two classes carry no
# extra data or behavior; they exist purely to be a distinct, catchable
# *type* of error.
class DocumentLoadError(Exception):
    """Base class: something went wrong turning a file into a Document."""


# Inheriting from DocumentLoadError (not directly from Exception) means
# `except DocumentLoadError:` catches BOTH this and its parent - the
# same is-a relationship Java exception hierarchies rely on, just
# without a `throws` clause anywhere forcing callers to handle it.
class UnsupportedFileTypeError(DocumentLoadError):
    """A file in docs/ isn't a type the loader knows how to parse."""

class TicketLoadError(Exception):
    """Something went wrong turning a tickets.csv row into a Ticket."""