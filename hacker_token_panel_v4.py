# hacker_token_panel_v4.py
# Single-file Flask app (Hacker Premium)
# - Multi-user login
# - Bulk real token check (Facebook Graph): debug_token + /me?fields=id,name
# - Neon "hacker" UI with ASCII banner
# - Per-user history (CSV) + history page + latest CSV download
# - Single file: run with Flask, deploy with gunicorn
#
# Quickstart:
#   pip install Flask==3.0.0 requests==2.32.3 gunicorn==22.0.0
#   export FLASK_SECRET_KEY="change_me"
#   python hacker_token_panel_v4.py
#
# Render/Fly Start Command:
#   gunicorn hacker_token_panel_v4:app

import os, io, csv, uuid, time, json, datetime, pathlib
from concurrent.futures import ThreadPoolExecutor, as_completed

from flask import Flask, request, session, redirect, url_for, send_file, render_template_string, flash
import requests

# ---------------------------- Config ----------------------------

APP_TITLE = "Harshu Token Ops"
HISTORY_DIR = pathlib.Path("history")
HISTORY_DIR.mkdir(exist_ok=True, parents=True)

# Simple multi-user store (edit here or set via USERS_JSON env var)
DEFAULT_USERS = {
    "admin": "pass123",
    "harshu": "loveu"
}
USERS = json.loads(os.environ.get("USERS_JSON", json.dumps(DEFAULT_USERS)))

# Limits & network
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "1500"))
MAX_WORKERS = int(os.environ.get("MAX_WORKERS", "20"))
DEFAULT_TIMEOUT = 15
MAX_RETRIES = 3
BACKOFF = 1.5

# Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change_this_secret")


# ---------------------------- Utils ----------------------------

def is_authed():
    return bool(session.get("user"))

def current_user():
    return session.get("user")

def ensure_user_history_dir(username: str) -> pathlib.Path:
    d = HISTORY_DIR / username
    d.mkdir(exist_ok=True, parents=True)
    return d

def mask_token_display(tok: str, mask: bool) -> str:
    if not mask: 
        return tok
    if len(tok) <= 12:
        return tok[:6] + "..."
    return tok[:8] + "..." + tok[-6:]

def http_get_json(url, params=None, timeout=DEFAULT_TIMEOUT):
    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.get(url, params=params, timeout=timeout)
            payload = r.json()
            if r.status_code >= 400:
                err = payload.get("error", {})
                return None, f"{err.get('type', 'HTTPError')}({r.status_code}): {err.get('message', 'Unknown error')}"
            if "error" in payload and payload["error"]:
                err = payload["error"]
                return None, f"{err.get('type', 'Error')}: {err.get('message', '')}"
            return payload, None
        except Exception as e:
            last_err = str(e)
            if attempt < MAX_RETRIES:
                time.sleep(BACKOFF ** attempt)
    return None, f"Retry failed: {last_err}"

def graph_debug_token(user_token: str, app_id: str, app_secret: str):
    url = "https://graph.facebook.com/debug_token"
    params = {
        "input_token": user_token.strip(),
        "access_token": f"{app_id}|{app_secret}"
    }
    payload, err = http_get_json(url, params=params)
    if err:
        return None, err
    return payload.get("data", {}), None

def graph_me_name(user_token: str):
    # Fetch user id & name with the token itself
    url = "https://graph.facebook.com/me"
    params = { "fields": "id,name", "access_token": user_token.strip() }
    payload, err = http_get_json(url, params=params)
    if err:
        return None, err
    return payload, None

def run_bulk_check(tokens, app_id, app_secret, mask_tokens=True):
    results = []
    def task(tok):
        data, err = graph_debug_token(tok, app_id, app_secret)
        row = {
            "token": mask_token_display(tok, mask_tokens),
            "is_valid": False,
            "user_id": "",
            "name": "",
            "expires_at": "",
            "app_id": "",
            "type": "",
            "application": "",
            "scopes": "",
            "error": ""
        }
        if err:
            row["error"] = err
            return row

        # Fill from debug_token
        if data:
            row.update({
                "is_valid": data.get("is_valid", False),
                "user_id": data.get("user_id", ""),
                "expires_at": data.get("expires_at", ""),
                "app_id": data.get("app_id", ""),
                "type": data.get("type", ""),
                "application": data.get("application", ""),
                "scopes": ",".join(data.get("scopes", [])) if isinstance(data.get("scopes"), list) else (data.get("scopes") or ""),
            })

        # If valid â†’ try to get name via /me
        if row["is_valid"]:
            me, err2 = graph_me_name(tok)
            if me and "name" in me:
                row["name"] = me.get("name", "")
                # If user_id absent, fill from /me
                if not row["user_id"] and "id" in me:
                    row["user_id"] = me.get("id", "")
            elif err2:
                # not fatal â€” keep as is
                row["error"] = (row["error"] + " | " if row["error"] else "") + f"me(): {err2}"
        return row

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = [ex.submit(task, t) for t in tokens]
        for f in as_completed(futures):
            results.append(f.result())

    # sort: valid first, then expiries
    def exp_key(r):
        try:
            return int(r.get("expires_at") or 0)
        except Exception:
            return 0
    results.sort(key=lambda r: (not r.get("is_valid", False), exp_key(r)))
    return results

def save_run(username, results, meta):
    user_dir = ensure_user_history_dir(username)
    run_id = datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
    csv_path = user_dir / f"{run_id}.csv"
    meta_path = user_dir / f"{run_id}.json"

    fields = ["token","is_valid","user_id","name","expires_at","app_id","type","application","scopes","error"]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(results)
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    return run_id, csv_path, meta_path

def list_runs(username):
    user_dir = ensure_user_history_dir(username)
    items = []
    for p in sorted(user_dir.glob("*.csv"), reverse=True):
        rid = p.stem
        meta = {}
        mp = user_dir / f"{rid}.json"
        if mp.exists():
            try:
                meta = json.loads(mp.read_text(encoding="utf-8"))
            except Exception:
                meta = {}
        items.append({
            "run_id": rid,
            "csv": str(p),
            "meta": meta
        })
    return items


# ---------------------------- Views ----------------------------

BANNER = r"""
â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
     âœ¦ Harshu Token Checker âœ¦  
       âš¡ Hatters ki maki chut â˜ ï¸ âš¡
â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
â•â•
"""

BASE_CSS = """
/* Hacker premium theme */
:root {
  --bg: #020a06;
  --card: rgba(4, 12, 8, 0.82);
  --fg: #d1fbd8;
  --muted: #86efac;
  --accent: #22c55e;
  --accent-2: #10b981;
  --danger: #f43f5e;
  --grid: #14351f;
}
* { box-sizing: border-box; }
html, body { height: 100%; }
body {
  margin: 0;
  background: radial-gradient(1200px 800px at 20% 10%, #001b10 0%, transparent 60%),
              radial-gradient(800px 600px at 80% 0%, #002710 0%, transparent 60%),
              var(--bg);
  color: var(--fg);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, "DejaVu Sans Mono", Consolas, "Liberation Mono", "Courier New", monospace;
  letter-spacing: 0.2px;
}

/* Matrix scanlines */
body::after{
  content:"";
  position:fixed; inset:0;
  background: repeating-linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.03) 1px, transparent 1px, transparent 3px);
  mix-blend-mode: overlay;
  pointer-events:none;
}

.banner {
  white-space: pre;
  text-align: center;
  color: #b7f7c6;
  text-shadow: 0 0 6px #22c55e, 0 0 18px #059669;
  padding: 10px 0 0 0;
  margin: 6px 0 0 0;
  user-select: text;
}

.topbar {
  display:flex; align-items:center; justify-content:space-between;
  padding: 10px 16px;
  border-bottom: 1px solid #123a24;
  background: linear-gradient(180deg, rgba(8,24,16,0.7), rgba(8,24,16,0.2));
  position: sticky; top:0; z-index: 50;
}
.brand { display:flex; align-items:center; gap:10px; }
.brand .dot {
  width:10px; height:10px; border-radius:50%; background: var(--accent);
  box-shadow: 0 0 14px var(--accent);
}
.brand h1 { font-size: 16px; margin: 0; color: var(--muted); }
.btn {
  appearance:none; border:1px solid #1a4a2e; color:var(--fg);
  background: linear-gradient(180deg, rgba(19,52,34,0.9), rgba(7,27,16,0.8));
  padding:10px 14px; border-radius:12px; cursor:pointer; text-decoration:none;
  box-shadow: inset 0 0 0 1px #0e2b1b, 0 0 20px rgba(34,197,94,0.12);
}
.btn:hover { filter: brightness(1.1); }
.btn.secondary { background: transparent; }
.btn.danger { border-color:#5e1120; color:#ffd6dd; background: linear-gradient(180deg, rgba(53,8,14,0.7), rgba(30,4,9,0.6)); }

.container { max-width: 1100px; margin: 12px auto 24px; padding: 0 16px; }

.card {
  background: var(--card);
  border: 1px solid #123a24;
  border-radius: 16px; padding: 18px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.35), inset 0 0 40px rgba(34, 197, 94, 0.05);
  backdrop-filter: blur(6px);
}

h2 { margin: 0 0 12px 0; font-size: 18px; color: #eafff1; }
label { font-size: 13px; color:#a7f3d0; display:block; margin-bottom:6px; }
input[type=text], input[type=password], textarea, input[type=file] {
  width: 100%; background: #07160e; color: var(--fg); border: 1px solid #164c2f;
  border-radius: 12px; padding: 10px 12px; outline: none;
}
textarea { min-height: 160px; resize: vertical; }
.row { display:grid; grid-template-columns: 1fr 1fr; gap:14px; }
.actions { display:flex; gap:10px; flex-wrap:wrap; }

/* Premium result table */
table { width:100%; border-collapse: collapse; font-size: 13px; }
th, td { text-align:left; padding: 10px; border-bottom: 1px dashed #123a24; }
tbody tr { transition: transform .12s ease, box-shadow .12s ease; }
tbody tr:hover { transform: scale(1.01); box-shadow: 0 0 20px rgba(34,197,94,0.12); background: rgba(34,197,94,0.06); }
.ok { color:#86efac; text-shadow: 0 0 6px #16a34a; }
.bad { color:#fda4af; text-shadow: 0 0 6px #be123c; }

footer { text-align:center; padding: 22px; color:#9ae6b4; opacity:0.9; }
footer a { color:#34d399; text-decoration: none; border-bottom: 1px dashed #34d399; }

.note { color:#9ae6b4; font-size:12px; opacity:0.8; }

.flash { margin-bottom: 12px; padding: 10px 12px; border-radius: 12px; }
.flash.error { background: rgba(244,63,94,0.12); border: 1px solid rgba(244,63,94,0.35); }
.flash.ok { background: rgba(34,197,94,0.12); border: 1px solid rgba(34,197,94,0.35); }

.switch { display:flex; gap:8px; align-items:center; }
input[type=checkbox]{ transform: scale(1.1); accent-color: #22c55e; }

/* Type-in reveal animation for table rows */
@keyframes reveal {
  from { opacity: 0; transform: translateY(4px); }
  to   { opacity: 1; transform: translateY(0); }
}
tbody tr { opacity: 0; animation: reveal .25s forwards; }
tbody tr:nth-child(1){ animation-delay: .02s;}
tbody tr:nth-child(2){ animation-delay: .04s;}
tbody tr:nth-child(3){ animation-delay: .06s;}
tbody tr:nth-child(4){ animation-delay: .08s;}
tbody tr:nth-child(5){ animation-delay: .10s;}
"""

BASE_LAYOUT = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ title or "Panel" }}</title>
  <style>{{ base_css }}</style>
</head>
<body>
  <div class="topbar">
    <div class="brand">
      <span class="dot"></span>
      <h1>[[ {{ app_title }} ]]</h1>
    </div>
    <div>
      {% if user %}
        <a class="btn secondary" href="{{ url_for('history') }}">History</a>
        <a class="btn danger" href="{{ url_for('logout') }}">Logout</a>
      {% endif %}
    </div>
  </div>

  <div class="container">
    <pre class="banner">{{ banner }}</pre>

    {% for cat, msg in flashes %}
      <div class="flash {{ 'error' if cat=='error' else 'ok' }}">{{ msg }}</div>
    {% endfor %}

    {{ body|safe }}
  </div>

  <footer>
    Made by <strong>Harshu</strong> with ðŸ’• love â€¢ 
    <a href="https://m.me/harshuuuxd" target="_blank">Message me on Facebook</a>
  </footer>
</body>
</html>
"""

LOGIN_PAGE = """
<div class="card" style="max-width:420px;margin:20px auto;">
  <h2>Login</h2>
  <form method="post">
    <label>Username</label>
    <input type="text" name="username" placeholder="enter username" required>
    <label style="margin-top:10px;">Password</label>
    <input type="password" name="password" placeholder="enter password" required>
    <div class="actions" style="margin-top:14px;">
      <button class="btn" type="submit">Enter system</button>
    </div>
    <div class="note" style="margin-top:10px;">Default: admin / pass123 (change via USERS_JSON or edit code)</div>
  </form>
</div>
"""

DASH_BODY = """
<div class="card">
  <h2>Bulk Token Checker</h2>
  <form method="post" enctype="multipart/form-data">
    <div class="row">
      <div>
        <label>Facebook App ID</label>
        <input type="text" name="app_id" placeholder="APP_ID" required>
      </div>
      <div>
        <label>Facebook App Secret</label>
        <input type="password" name="app_secret" placeholder="APP_SECRET" required>
      </div>
    </div>

    <div style="margin-top:12px;">
      <label>Tokens (one per line)</label>
      <textarea name="tokens" placeholder="EAAD6V7..."></textarea>
    </div>

    <div class="actions" style="align-items:center;justify-content:space-between;margin-top:10px;">
      <div class="switch">
        <input type="checkbox" id="mask_tokens" name="mask_tokens" checked>
        <label for="mask_tokens">Mask tokens on screen</label>
      </div>
      <div>
        <input type="file" name="tokens_file" accept=".txt">
      </div>
    </div>

    <div class="actions" style="margin-top:12px;">
      <button class="btn" type="submit">Run Check</button>
      {% if last_download %}
        <a class="btn secondary" href="{{ url_for('download_latest') }}">Download last CSV</a>
      {% endif %}
    </div>
    <div class="note" style="margin-top:6px;">Limit: {{ max_tokens }} tokens per run â€¢ parallel {{ max_workers }} threads â€¢ retries x{{ retries }}</div>
  </form>
</div>

{% if results %}
<div class="card" style="margin-top:16px;">
  <h2>Results</h2>
  <input id="q" type="text" placeholder="type to filter..." style="margin-bottom:10px;">
  <div style="overflow:auto;">
    <table id="tbl">
      <thead>
        <tr>
          <th>Token</th>
          <th>Valid</th>
          <th>User ID</th>
          <th>Name</th>
          <th>Expires At (epoch)</th>
          <th>Expires (local)</th>
          <th>App ID</th>
          <th>Type</th>
          <th>Application</th>
          <th>Scopes</th>
          <th>Error</th>
        </tr>
      </thead>
      <tbody>
        {% for r in results %}
        <tr>
          <td>{{ r.token }}</td>
          <td class="{{ 'ok' if r.is_valid else 'bad' }}">{{ 'âœ…' if r.is_valid else 'âŒ' }}</td>
          <td>{{ r.user_id }}</td>
          <td>{{ r.name }}</td>
          <td class="epoch">{{ r.expires_at }}</td>
          <td class="human">-</td>
          <td>{{ r.app_id }}</td>
          <td>{{ r.type }}</td>
          <td>{{ r.application }}</td>
          <td>{{ r.scopes }}</td>
          <td class="bad">{{ r.error }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  <div class="actions" style="margin-top:12px;">
    <a class="btn" href="{{ url_for('download_latest') }}">Download CSV</a>
  </div>
</div>

<script>
// filter
const q = document.getElementById('q');
const rows = Array.from(document.querySelectorAll('#tbl tbody tr'));
q.addEventListener('input', () => {
  const val = q.value.toLowerCase();
  rows.forEach(tr => {
    tr.style.display = tr.innerText.toLowerCase().includes(val) ? '' : 'none';
  });
});
// epoch -> local
document.querySelectorAll('#tbl tbody tr').forEach(tr => {
  const e = tr.querySelector('.epoch').innerText.trim();
  const human = tr.querySelector('.human');
  const num = parseInt(e || '0', 10);
  human.innerText = num > 0 ? (new Date(num * 1000)).toLocaleString() : '-';
});
</script>
{% endif %}
"""

HISTORY_BODY = """
<div class="card">
  <h2>Run History</h2>
  <div class="note">User: <strong>{{ user }}</strong></div>
  {% if items %}
  <div style="overflow:auto; margin-top:10px;">
    <table>
      <thead>
        <tr>
          <th>Run ID</th>
          <th>When</th>
          <th>Total</th>
          <th>Valid</th>
          <th>Invalid</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {% for it in items %}
        <tr>
          <td>{{ it.run_id }}</td>
          <td>{{ it.meta.when }}</td>
          <td>{{ it.meta.total }}</td>
          <td class="ok">{{ it.meta.valid }}</td>
          <td class="bad">{{ it.meta.invalid }}</td>
          <td>
            <a class="btn" href="{{ url_for('download_run', run_id=it.run_id) }}">Download CSV</a>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  {% else %}
    <div class="note" style="margin-top:8px;">No runs yet. Go to dashboard and run a check.</div>
  {% endif %}
  <div class="actions" style="margin-top:12px;">
    <a class="btn secondary" href="{{ url_for('dashboard') }}">Back to Dashboard</a>
  </div>
</div>
"""

def render_page(body_html, title="Panel"):
    flashes = list(getattr(request, "_flashes", []) or [])
    session.modified = True
    tmpl = render_template_string(
        BASE_LAYOUT,
        base_css=BASE_CSS,
        title=title,
        body=body_html,
        flashes=flashes,
        user=current_user(),
        app_title=APP_TITLE,
        banner=BANNER
    )
    return tmpl

# ---------------------------- Routes ----------------------------

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username", "").strip()
        p = request.form.get("password", "").strip()
        if u in USERS and USERS[u] == p:
            session["user"] = u
            return redirect(url_for("dashboard"))
        flash("Invalid username or password", "error")
    return render_page(LOGIN_PAGE, title="Login")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if not is_authed():
        return redirect(url_for("login"))

    results = None
    last_download = session.get("last_csv_path")

    if request.method == "POST":
        app_id = request.form.get("app_id", "").strip()
        app_secret = request.form.get("app_secret", "").strip()
        mask_tokens = bool(request.form.get("mask_tokens"))
        tokens_text = request.form.get("tokens", "").strip()

        tokens = []
        if tokens_text:
            tokens.extend([t.strip() for t in tokens_text.splitlines() if t.strip()])

        file = request.files.get("tokens_file")
        if file and file.filename:
            try:
                content = file.read().decode("utf-8", errors="ignore")
                tokens.extend([t.strip() for t in content.splitlines() if t.strip()])
            except Exception as e:
                flash(f"File read error: {e}", "error")

        tokens = list(dict.fromkeys(tokens))

        if not app_id or not app_secret:
            flash("App ID and App Secret required.", "error")
        elif not tokens:
            flash("Provide at least one token.", "error")
   
