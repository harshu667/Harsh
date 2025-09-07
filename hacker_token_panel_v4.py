# hacker_token_panel_v4.py
# Premium Token Checker with Login + Copy Alive Tokens + Logout

import requests
from flask import Flask, request, session, redirect, url_for, render_template_string

APP_TITLE = "Harshu Token Checker Tool"
USERS = {"admin": "pass123"}  # login credentials

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------------- Utils ----------------
def is_authed():
    return "user" in session

def mask_token(tok: str) -> str:
    if len(tok) <= 14:
        return tok[:6] + "..."
    return tok[:8] + "..." + tok[-6:]

def check_token(token: str):
    try:
        r = requests.get("https://graph.facebook.com/me",
                         params={"access_token": token}, timeout=10)
        data = r.json()
        if "id" in data:
            return {"status": "valid", "id": data["id"], "name": data.get("name", "")}
        elif "error" in data:
            return {"status": "invalid", "id": None, "name": None}
        else:
            return {"status": "error", "id": None, "name": None}
    except Exception:
        return {"status": "error", "id": None, "name": None}

# ---------------- Routes ----------------
@app.route("/")
def root():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")
        if u in USERS and USERS[u] == p:
            session["user"] = u
            return redirect(url_for("dashboard"))
        else:
            return render_template_string(LOGIN_HTML, title=APP_TITLE, error="❌ Invalid username/password")
    return render_template_string(LOGIN_HTML, title=APP_TITLE, error=None)

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if not is_authed():
        return redirect(url_for("login"))

    results, summary, alive_tokens = [], None, []
    if request.method == "POST":
        tokens = request.form.get("tokens", "").strip().splitlines()
        tokens = [t.strip() for t in tokens if t.strip()]
        active, dead, error = 0, 0, 0
        for tok in tokens:
            res = check_token(tok)
            if res["status"] == "valid":
                active += 1
                alive_tokens.append(tok)
            elif res["status"] == "invalid":
                dead += 1
            else:
                error += 1
            results.append({
                "token": mask_token(tok),
                "status": res["status"],
                "id": res["id"],
                "name": res["name"]
            })
        summary = {"total": len(tokens), "active": active, "dead": dead, "error": error}

    return render_template_string(DASHBOARD_HTML, title=APP_TITLE, user=session["user"],
                                  results=results, summary=summary, alive_tokens=alive_tokens)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------- HTML Templates ----------------
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>{{title}} - Login</title>
  <style>
    body { background:black; color:#00ffcc; font-family: monospace; display:flex; align-items:center; justify-content:center; height:100vh; }
    .card { background:rgba(0,255,128,0.1); padding:30px; border:2px solid #00ffcc; border-radius:12px; box-shadow:0 0 20px #00ffcc; text-align:center; }
    h2 { color:#00ffcc; text-shadow:0 0 8px #00ffcc; }
    input { width:80%; padding:8px; margin:10px 0; border:1px solid #00ffcc; background:black; color:#00ffcc; border-radius:6px; }
    button { background:#00ffcc; border:none; padding:10px 20px; color:black; font-weight:bold; cursor:pointer; border-radius:6px; }
    button:hover { box-shadow:0 0 15px #00ffcc; }
    a { color:#00ffcc; text-decoration:none; }
    a:hover { text-decoration:underline; }
  </style>
</head>
<body>
  <div class="card">
    <h2>🔐 Harshu Token Checker Login</h2>
    {% if error %}<p style="color:red">{{error}}</p>{% endif %}
    <form method="post">
      <input name="username" placeholder="Username"><br>
      <input name="password" type="password" placeholder="Password"><br>
      <button type="submit">Login</button>
    </form>
    <p><a href="https://m.me/harshuuuxd" target="_blank">📩 Contact Me</a></p>
  </div>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>{{title}} - Dashboard</title>
  <style>
    body { background:black; color:#00ffcc; font-family: monospace; }
    .banner { text-align:center; margin:20px; font-size:20px; text-shadow:0 0 10px #00ffcc; }
    textarea { width:90%; height:120px; background:black; color:#00ffcc; border:2px solid #00ffcc; border-radius:8px; padding:10px; }
    button { background:#00ffcc; border:none; padding:10px 20px; margin-top:10px; color:black; font-weight:bold; cursor:pointer; border-radius:6px; }
    button:hover { box-shadow:0 0 15px #00ffcc; }
    table { width:95%; margin:20px auto; border-collapse:collapse; }
    th, td { border:1px solid #00ffcc; padding:8px; text-align:center; }
    tr:nth-child(even) { background:rgba(0,255,128,0.1); }
    .summary { margin:20px auto; padding:10px; border:2px solid #00ffcc; border-radius:8px; width:60%; text-align:center; }
    .footer { text-align:center; margin-top:30px; font-size:14px; color:#00ffcc; }
    a { color:#00ffcc; text-decoration:none; }
  </style>
  <script>
    function copyAlive() {
      var txt = document.getElementById("aliveTokens");
      txt.style.display = "block";
      txt.select();
      document.execCommand("copy");
      txt.style.display = "none";
      alert("✅ Alive tokens copied!");
    }
  </script>
</head>
<body>
  <div class="banner">
    ══════════════════════════════════<br>
     ✦ Harshu Token Checker ✦<br>
       ⚡ Hatters ki maki chut ☠️⚡<br>
    ══════════════════════════════════
  </div>
  <div style="text-align:center;">
    <form method="post">
      <textarea name="tokens" placeholder="Enter tokens here (one per line)..."></textarea><br>
      <button type="submit">Check Tokens</button>
    </form>
  </div>
  {% if summary %}
  <div class="summary">
    <b>Total:</b> {{summary.total}} |
    ✅ Active: {{summary.active}} |
    ❌ Dead: {{summary.dead}} |
    ⚠️ Errors: {{summary.error}}
    {% if summary.active > 0 %}
      <br><br>
      <button onclick="copyAlive()">📋 Copy Alive Tokens</button>
      <textarea id="aliveTokens" style="display:none;">{% for t in alive_tokens %}{{t}}&#10;{% endfor %}</textarea>
    {% endif %}
  </div>
  <table>
    <tr><th>Masked Token</th><th>Status</th><th>User ID</th><th>Name</th></tr>
    {% for r in results %}
      <tr>
        <td>{{r.token}}</td>
        <td>
          {% if r.status == 'valid' %}✅ Valid{% elif r.status == 'invalid' %}❌ Invalid{% else %}⚠️ Error{% endif %}
        </td>
        <td>{{r.id if r.id else '-'}}</td>
        <td>{{r.name if r.name else '-'}}</td>
      </tr>
    {% endfor %}
  </table>
  {% endif %}
  <div class="footer">
    Made with ❤️ by Harshu | 
    <a href="https://m.me/harshuuuxd" target="_blank">Contact Me</a> | 
    <a href="{{ url_for('logout') }}">🚪 Logout</a>
  </div>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
    
