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

APP_TITLE = "Harshu Token Checker Tool"
HISTORY_DIR = pathlib.Path("history")
HISTORY_DIR.mkdir(exist_ok=True, parents=True)

# ✅ Updated credentials
DEFAULT_USERS = {
    "harshu001": "harshking90"
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

        if row["is_valid"]:
            me, err2 = graph_me_name(tok)
            if me and "name" in me:
                row["name"] = me.get("name", "")
                if not row["user_id"] and "id" in me:
                    row["user_id"] = me.get("id", "")
            elif err2:
                row["error"] = (row["error"] + " | " if row["error"] else "") + f"me(): {err2}"
        return row

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = [ex.submit(task, t) for t in tokens]
        for f in as_completed(futures):
            results.append(f.result())

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

# ---------------------------- Views + Routes ----------------------------
# (⚡ same as before, no change, code continues...)

# 🔥 At the end you already had:
# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000, debug=True)
