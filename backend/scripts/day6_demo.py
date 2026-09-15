"""
Day 6 demo script: run today's ticket-summary chain against real
tickets already loaded by the existing ingestion layer, the same way
scripts/day2_demo.py exercised the loaders before any API existed
around them.

Run from backend\\, with Ollama running (`ollama serve`, or the
desktop app's background service) and the venv active:
    python scripts/day6_demo.py
"""

from app.ai.chains import summarize_ticket
from app.ingestion.ticket_loader import load_tickets_from_csv


def main() -> None:
    tickets = load_tickets_from_csv("tickets.csv")
    for ticket in tickets:
        summary = summarize_ticket(
            title=ticket.title,
            priority=ticket.priority.value,
            status=ticket.status.value,
        )
        print(f"[Ticket {ticket.id}] {summary}")


if __name__ == "__main__":
    main()