# Property Dot Com CRM — starter

A local development foundation for Property Dot Com's lead register and future
agent workflows. This is a new codebase, not a migration of existing CRM records.
No real client records are bundled or imported.

## Technical direction

Python 3.11+ standard library + SQLite + server-rendered HTML. No pip packages,
JavaScript build chain, cloud account, API keys or paid services are needed.
This keeps an empty repository easy to run and the lead module reusable.
See [architecture and next steps](docs/architecture.md) for limits and decisions.

## Setup

1. Install Python 3.11+ with timezone data (normally included on Linux/macOS).
   On Windows, if `ZoneInfoNotFoundError` occurs, run `py -m pip install tzdata`.
2. Clone and enter this repository:
   ```sh
   git clone https://github.com/kharpudedk-cmd/testRepo.git
   cd testRepo
   ```
3. Start from the repository root:
   ```sh
   python3 -m app
   ```
   On Windows use `py -m app` instead.
4. Open **http://127.0.0.1:8000** on the same computer. Stop with Ctrl+C.
   For a busy port: `python3 -m app --port 8001`.

The database is created automatically at `data/crm.sqlite3` and survives restarts.
Run from the repository root so this relative location stays consistent. Optionally
set `CRM_DB_PATH` to an absolute file path before starting. It is not a `.env` loader.
No credentials are configured. The server binds to loopback only; this is not a
hosted/mobile/shared CRM. Do not expose it to a network or use it as production.

## Lead register

Add date, client, phone, Rental/Resale/Purchase/Other, property/location,
optional budget in **whole INR**, notes and an assigned agent label.
For example, enter `17000000` for ₹1.70 crore; blank means unknown, not zero.
New entries start at `New Lead`. Search client/phone/location, filter status,
and update status or assigned agent. Dates default to India time; phones are text.
Separate enquiries may intentionally share a phone, so no automatic deduplication
or merging is performed. Full editing, deletion, import/export and follow-up
reminders are future work. Agent labels do not trigger automation.

## Structure

```text
app/
  __main__.py          Local HTTP interface
  leads/register.py    Validation and SQLite lead register
  agents/README.md     Future agent-work boundary
data/                 Ignored runtime database (no client data in git)
docs/architecture.md   Decisions, limitations and development sequence
tests/                 Isolated storage and HTTP checks
```

## Verify

```sh
python3 -m unittest discover -s tests -v
python3 -m compileall -q app tests
```

Tests use temporary databases and fictional records. No external services run.

## Data handling

The repository is public. Never commit real leads, phone lists, database files,
credentials or exports. `.gitignore` excludes runtime databases; it cannot protect
personal data manually pasted into source or documentation. Back up the SQLite
file outside git **after stopping the app**, and test restoring that copy.
This starter has no login, roles, audit trail, encryption or automated backup.
