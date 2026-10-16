# Architecture decision 001: local, dependency-light starter

Status: initial implementation; revisit before shared use.

## Scope and separation

`app.leads.register.LeadRegister` owns input validation and parameterized SQL.
The HTML adapter only parses requests, renders escaped values and redirects after
writes. SQLite persistence lives outside source files. `app/agents` documents a
future integration boundary; no autonomous worker is started.

A single Python process and SQLite are sufficient to review the initial workflow.
Choosing React, an API framework, Postgres, cloud hosting or an AI provider now
would impose unconfirmed operating requirements. The stdlib HTTP server is strictly
a local development adapter and must be replaced before deployment.

## Current contract

- Integer ID; enquiry date as ISO date; UTC `created_at` from SQLite.
- Required client, phone, location and lead type; optional integer INR budget,
  notes and assigned-agent label. India timezone supplies the UI default date.
- Explicit finite statuses, new records defaulting to New Lead.
- SQL parameters, escaped HTML, request size cap and per-process form token.
- No seeded clients, account connection, outbound messages or background jobs.

The form token reduces cross-site form writes; it is not authentication. Any local
process/user able to reach the app can read or modify records. SQLite files are
unencrypted. All updates are last-write-wins and there is no activity history.
The schema uses CREATE TABLE IF NOT EXISTS, not a migration system. Once schema
changes start, introduce versioned migrations and backup/restore verification.

## Next development sequence

1. Confirm enquiry fields, budget conventions and status lifecycle with the team.
2. Add stable agent IDs, follow-up dates, tasks, full edit and activity history.
3. Design duplicate review and validated import/export against existing records.
4. Before shared access: authentication, roles, audit logs, migrations, backups,
   retention rules, production HTTP framework and deployment tests.
5. Only after provider and permissions decisions: email/WhatsApp/calling adapters
   and queue-backed AI tasks with reviewable drafts and explicit send controls.

No deployment target, production database, paid subscription, business SLA or
existing-record migration is assumed by this starter.
