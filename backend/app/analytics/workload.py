"""
Analytics: Team Workload Distribution (Business Question #3).

Deliberately its own module, the same way app/ingestion/document_loader.py
is - a focused piece that knows how to answer ONE question, given plain
data, with no FastAPI or web awareness at all. KnowledgeBaseService
calls into this; it doesn't contain the pandas/numpy logic itself.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.models import Ticket, User

# Mirrors app.models.enums.TicketPriority exactly. Kept as a plain dict
# (not derived from the enum automatically) so that adding a new
# TicketPriority value without updating this mapping fails LOUDLY
# (see the assertion in Step 4) instead of silently under-counting
# that ticket's weight.
PRIORITY_WEIGHT = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}

OPEN_STATUSES = {"Open", "In-Progress"}


#we are using the prefix _ to indicate that these functions are intended for internal use within the module
#not meant to be called directly by external code.
def _tickets_to_frame(tickets: list[Ticket]) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "id": ticket.id,
            "priority": ticket.priority.value,
            "status": ticket.status.value,
            "assignee_id": ticket.assignee_id,
        }
        for ticket in tickets
    ])


def _users_to_frame(users: list[User]) -> pd.DataFrame:
    return pd.DataFrame([{"id": user.id, "team": user.team} for user in users])

def compute_team_workload(tickets: list[Ticket], users: list[User]) -> dict:
    """
    For every team with at least one OPEN or IN-PROGRESS ticket:
    how many such tickets it has, a priority-weighted "load score"
    (Low=1 ... Critical=4, summed), that team's share of the total
    load across all teams, and whether its load is a statistical
    outlier (more than one standard deviation above the mean).
    """
    tickets_df = _tickets_to_frame(tickets)
    users_df = _users_to_frame(users)

    #the merge function acts similarly to a join in SQL
    merged = tickets_df.merge(
        users_df, left_on="assignee_id", right_on="id", suffixes=("_ticket", "_user")
    )

    #here we filter the merged dataframe to only include tickets that have an open status
    open_tickets = merged[merged["status"].isin(OPEN_STATUSES)].copy()
    #then, we map the priority values to their corresponding weights
    open_tickets["priority_weight"] = open_tickets["priority"].map(PRIORITY_WEIGHT)

    #then we group tickets by team and calculate the number of tickets and total load score for each team
    counts = open_tickets.groupby("team").size()
    load = open_tickets.groupby("team")["priority_weight"].sum()

    #next, we convert the team names and load values to numpy arrays for further calculations
    teams = load.index.to_numpy()
    load_array = load.to_numpy(dtype=float)

    #then we calculate the total load, share percentage, mean load, and standard deviation of the load
    total_load = float(np.sum(load_array)) if load_array.size else 0.0
    share_pct = (load_array / total_load * 100) if total_load > 0 else np.zeros_like(load_array)
    mean_load = float(np.mean(load_array)) if load_array.size else 0.0
    std_load = float(np.std(load_array)) if load_array.size else 0.0
    overloaded = load_array > (mean_load + std_load)

    #finally, we can construct a report for each team
    team_reports = [
        {
            "team": str(team),
            "open_ticket_count": int(counts[team]),
            "load_score": float(load_array[i]),
            "load_share_pct": float(share_pct[i]),
            "is_overloaded": bool(overloaded[i]),
        }
        for i, team in enumerate(teams)
    ]

    return {
        "teams": team_reports,
        "total_open_tickets": int(len(open_tickets)),
        "mean_load_score": mean_load,
        "std_load_score": std_load,
    }