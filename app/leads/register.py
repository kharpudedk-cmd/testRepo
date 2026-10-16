"""Lead validation and SQLite storage, independent of the web interface."""
import sqlite3
from datetime import date
from pathlib import Path

TYPES = ("Rental", "Resale", "Purchase", "Other")
STATUSES = ("New Lead", "Contacted", "Visit Scheduled", "Negotiation", "Closed", "Lost")

class LeadRegister:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY, lead_date TEXT NOT NULL,
                client TEXT NOT NULL, phone TEXT NOT NULL, lead_type TEXT NOT NULL,
                location TEXT NOT NULL, budget_inr INTEGER, status TEXT NOT NULL,
                notes TEXT NOT NULL, assigned_agent TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")

    def connect(self):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        return db

    def add(self, values):
        fields = {k: str(values.get(k, "")).strip() for k in
                  ("lead_date", "client", "phone", "lead_type", "location", "notes", "assigned_agent")}
        for key in ("client", "phone", "location"):
            if not fields[key]:
                raise ValueError(f"{key} is required")
        if any(len(value) > 2000 for value in fields.values()):
            raise ValueError("Each field must be at most 2000 characters")
        try:
            date.fromisoformat(fields["lead_date"])
        except ValueError:
            raise ValueError("Lead date must be YYYY-MM-DD") from None
        if fields["lead_type"] not in TYPES:
            raise ValueError("Unknown lead type")
        raw = str(values.get("budget_inr", "")).strip()
        if raw and (not raw.isascii() or not raw.isdigit()):
            raise ValueError("Budget must be a whole non-negative INR amount")
        budget = int(raw) if raw else None
        if budget is not None and budget > 9223372036854775807:
            raise ValueError("Budget exceeds supported amount")
        fields.update(budget_inr=budget, status="New Lead")
        columns = tuple(fields)
        with self.connect() as db:
            cursor = db.execute(f"INSERT INTO leads ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",
                                tuple(fields.values()))
            return cursor.lastrowid

    def list(self, query="", status=""):
        if status and status not in STATUSES:
            raise ValueError("Unknown status")
        with self.connect() as db:
            return [dict(row) for row in db.execute("""SELECT * FROM leads
                WHERE (? = '' OR instr(lower(client || ' ' || phone || ' ' || location), lower(?)) > 0)
                AND (? = '' OR status = ?) ORDER BY lead_date DESC, id DESC""",
                (query, query, status, status))]

    def update(self, lead_id, status, assigned_agent):
        if status not in STATUSES:
            raise ValueError("Unknown status")
        if len(assigned_agent) > 2000:
            raise ValueError("Agent label is too long")
        with self.connect() as db:
            result = db.execute("UPDATE leads SET status=?, assigned_agent=? WHERE id=?",
                                (status, assigned_agent.strip(), lead_id))
            if result.rowcount != 1:
                raise ValueError("Lead not found")
