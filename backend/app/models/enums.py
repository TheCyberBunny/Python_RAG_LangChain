"""
DevMate - Northbeam Engineering Assistant
Day 1 - Enumerated types shared across all domain models.
"""

from enum import Enum  # Enum is Python's version of a Java `enum` type


class DocumentCategory(str, Enum):
    # Inheriting from (str, Enum) means each member IS a string too -
    # DocumentCategory.RUNBOOK == "Runbook" evaluates to True. This is
    # what makes these values easy to send as JSON later this week.
    RUNBOOK = "Runbook"
    WIKI = "Wiki"
    POSTMORTEM = "Postmortem"
    ONBOARDING = "Onboarding"


class TicketPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class TicketStatus(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "In-Progress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"