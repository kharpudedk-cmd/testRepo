"""Local-only development interface. Run: python3 -m app."""
import argparse
import os
import secrets
from datetime import datetime
from zoneinfo import ZoneInfo
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit
from app.leads.register import LeadRegister, TYPES, STATUSES

TOKEN = secrets.token_urlsafe(32)

def options(items, selected=""):
    return "".join(f'<option{ " selected" if item == selected else ""}>{escape(item)}</option>' for item in items)

def field(name, label, value="", kind="text", required=False):
    return f'<label>{label}<input name="{name}" type="{kind}" value="{escape(value, quote=True)}" {"required" if required else ""}></label>'

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # Avoid writing lead searches or personal data to access logs.

    def send_html(self, body, status=200):
        page = """<!doctype html><html lang="en"><meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Property Dot Com CRM</title><style>
        body{font:16px system-ui;max-width:1200px;margin:24px auto;padding:0 18px;background:#f5f7fb;color:#17213a}
        form{background:white;padding:16px;margin:12px 0;border-radius:10px}label{display:inline-block;margin:8px}
        input,select,textarea,button{font:inherit;padding:8px;max-width:100%;box-sizing:border-box}input{display:block}
        table{border-collapse:collapse;width:100%;background:white}td,th{padding:10px;text-align:left;border-bottom:1px solid #ddd}
        .scroll{overflow:auto}button{cursor:pointer}textarea{display:block;width:100%}</style>""" + body + '</html>'
        data = page.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urlsplit(self.path)
        if url.path != "/":
            return self.send_html("Not found", 404)
        params = parse_qs(url.query)
        query = params.get("q", [""])[0]
        status = params.get("status", [""])[0]
        try:
            leads = self.server.register.list(query, status)
        except ValueError as error:
            return self.send_html(escape(str(error)), 400)
        today = datetime.now(ZoneInfo("Asia/Kolkata")).date().isoformat()
        token = f'<input type="hidden" name="token" value="{TOKEN}">'
        body = '<h1>Property Dot Com CRM</h1><p>Local development starter · Lead register</p>'
        body += '<h2>Add lead</h2><form method="post" action="/leads">' + token
        for args in [("lead_date", "Lead date (India)", today, "date", True),
                     ("client", "Client", "", "text", True), ("phone", "Phone", "", "tel", True),
                     ("location", "Property / location", "", "text", True),
                     ("budget_inr", "Budget (whole INR; optional)", "", "number", False),
                     ("assigned_agent", "Assigned agent", "", "text", False)]:
            body += field(*args)
        body += f'<label>Type <select name="lead_type">{options(TYPES)}</select></label>'
        body += '<label>Notes<textarea name="notes" maxlength="2000"></textarea></label><button>Add lead</button></form>'
        body += '<form method="get">' + field("q", "Search client, phone or location", query)
        body += f'<select name="status">{options(("",) + STATUSES, status)}</select><button>Filter</button> <a href="/">Reset</a></form>'
        body += f'<h2>Lead register ({len(leads)})</h2><div class="scroll"><table><tr><th>Date / ID</th><th>Client / phone</th><th>Property / type</th><th>Budget INR / notes</th><th>Status / assigned agent</th></tr>'
        for lead in leads:
            e = {key: escape(str(value if value is not None else ""), quote=True) for key, value in lead.items()}
            body += f'<tr><td>{e["lead_date"]}<br>#{e["id"]}</td><td>{e["client"]}<br>{e["phone"]}</td><td>{e["location"]}<br>{e["lead_type"]}</td><td>{e["budget_inr"]}<br>{e["notes"]}</td><td>'
            body += f'<form method="post" action="/leads/update">{token}<input type="hidden" name="id" value="{e["id"]}"><select name="status">{options(STATUSES, lead["status"])}</select>'
            body += field("assigned_agent", "Agent", lead["assigned_agent"]) + '<button>Save</button></form></td></tr>'
        body += '</table></div>'
        if not leads:
            body += '<p>No matching leads. Add a lead above to begin.</p>'
        self.send_html(body)

    def do_POST(self):
        if self.path not in ("/leads", "/leads/update"):
            return self.send_html("Not found", 404)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 32768:
                return self.send_html("Invalid request size", 413)
            values = {key: items[0] for key, items in parse_qs(self.rfile.read(length).decode(), keep_blank_values=True).items()}
            if not secrets.compare_digest(values.pop("token", ""), TOKEN):
                return self.send_html("Invalid form token. Reload the page.", 403)
            if self.path == "/leads":
                self.server.register.add(values)
            else:
                self.server.register.update(int(values.get("id", "")), values.get("status", ""), values.get("assigned_agent", ""))
        except (ValueError, UnicodeError) as error:
            return self.send_html(f'<p>{escape(str(error))}</p><a href="/">Back to register</a>', 400)
        self.send_response(303)
        self.send_header("Location", "/")
        self.end_headers()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    register = LeadRegister(os.environ.get("CRM_DB_PATH", "data/crm.sqlite3"))
    server = HTTPServer(("127.0.0.1", args.port), Handler)
    server.register = register
    print(f"Property Dot Com CRM: http://127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == "__main__":
    main()
