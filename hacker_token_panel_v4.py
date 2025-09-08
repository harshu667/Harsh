# hacker_token_panel_v4.py
# Premium Hacker Style Token Checker (Neon Glassmorphism Look)

import requests
from flask import Flask, request, session, redirect, url_for, render_template_string

APP_TITLE = "Harshu Token Checker Tool"
USERS = {"Harshu00": "Harshu_don"}  # login credentials

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
    body {
      margin:0;
      height:100vh;
      display:flex;
      justify-content:center;
      align-items:center;
      background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
      font-family: 'Poppins', sans-serif;
      color:white;
    }
    .login-box {
      background: rgba(255,255,255,0.05);
      backdrop-filter: blur(12px);
      border-radius:20px;
      padding:40px 30px;
      text-align:center;
      width:340px;
      box-shadow:0 0 25px rgba(0,255,255,0.4);
      border:1px solid rgba(0,255,255,0.2);
    }
    h2 {
      font-size:26px;
      margin-bottom:25px;
      font-weight:700;
      color:#fff;
      text-shadow:0 0 15px #00ffff, 0 0 30px #ff00ff;
    }
    input {
      width:100%;
      padding:12px;
      margin:10px 0;
      border:none;
      border-radius:12px;
      outline:none;
      background:rgba(0,0,0,0.3);
      color:#fff;
      font-size:15px;
      border:1px solid rgba(0,255,255,0.3);
      transition:0.3s;
    }
    input:focus {
      border-color:#00ffff;
      box-shadow:0 0 10px #00ffff;
    }
    button {
      width:100%;
      padding:12px;
      margin-top:15px;
      background: linear-gradient(90deg,#ff00cc,#00ffff);
      border:none;
      border-radius:12px;
      color:white;
      font-weight:bold;
      font-size:16px;
      cursor:pointer;
      transition:0.3s;
    }
    button:hover {
      transform:scale(1.05);
      box-shadow:0 0 20px #ff00cc, 0 0 25px #00ffff;
    }
    .footer {
      margin-top:18px;
      font-size:13px;
      color:#ccc;
    }
    .footer span {
      background: linear-gradient(90deg,#ff00cc,#00ffff);
      -webkit-background-clip: text;
      color: transparent;
      font-weight:bold;
    }
    .footer a {
      display:block;
      margin-top:5px;
      text-decoration:none;
      color:#00ffff;
      font-weight:bold;
    }
  </style>
</head>
<body>
  <div class="login-box">
    <h2>Login to continue</h2>
    {% if error %}<p style="color:red">{{error}}</p>{% endif %}
    <form method="post">
      <input type="text" name="username" placeholder="Username" required>
      <input type="password" name="password" placeholder="Password" required>
      <button type="submit">Login</button>
    </form>
    <div class="footer">
      Made with ❤️ by <span>Harshu</span><br>
      <a href="https://m.me/harshuuuxd" target="_blank">📩 Contact Me</a>
    </div>
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
    body { margin:0; background:black; color:#00ffcc; font-family: monospace; display:flex; flex-direction:column; min-height:100vh; }
    .container { flex:1; display:flex; flex-direction:column; align-items:center; justify-content:flex-start; padding:20px; }
    .banner { text-align:center; font-size:22px; font-weight:bold; margin-bottom:20px; color:#ff00cc; text-shadow:0 0 15px #00ffff; }
    textarea { width:90%; max-width:700px; height:120px; background:black; color:#00ffcc; border:2px solid #00ffcc; border-radius:8px; padding:10px; }
    button { background: linear-gradient(90deg,#ff00cc,#00ffff); border:none; padding:10px 20px; margin-top:10px; color:white; font-weight:bold; cursor:pointer; border-radius:6px; }
    button:hover { box-shadow:0 0 15px #ff00cc, 0 0 15px #00ffff; }
    .summary { margin:20px auto; padding:15px; border-radius:12px; width:70%; text-align:center; max-width:500px;
               background:rgba(255,255,255,0.05); backdrop-filter:blur(10px); box-shadow:0 0 20px rgba(0,255,255,0.3); }
    .card { background:rgba(0,255,128,0.05); border:1px solid #00ffcc; border-radius:12px; padding:12px; margin:10px auto; width:90%; max-width:700px; box-shadow:0 0 12px #00ffcc; }
    .footer { text-align:center; padding:12px; font-size:14px; color:#00ffcc; border-top:1px solid #00ffcc; margin-top:20px; }
    .footer a { color:#ff00cc; font-weight:bold; text-decoration:none; }
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
  <div class="container">
    <div class="banner">
      ✦ Harshu Token Checker ✦ <br>
      <span style="color:#ff4444; text-shadow:0 0 10px #ff0000;">⚡ Haters ki maki chut ☠️⚡</span>
    </div>
    <form method="post">
      <textarea name="tokens" placeholder="Enter tokens here (one per line)..."></textarea><br>
      <button type="submit">Check Tokens</button>
    </form>
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
    {% for r in results %}
      <div class="card">
        <b>🔑 Token:</b> {{r.token}} <br>
        <b>Status:</b>
        {% if r.status == 'valid' %}✅ Valid{% elif r.status == 'invalid' %}❌ Invalid{% else %}⚠️ Error{% endif %}<br>
        <b>User ID:</b> {{r.id if r.id else '-' }} <br>
        <b>Name:</b> {{r.name if r.name else '-' }}
      </div>
    {% endfor %}
    {% endif %}
  </div>
  <div class="footer">

    Made with ❤️ by Harshu | <a href="https://m.me/harshuuuxd" target="_blank">📩 Contact Me</a> | <a href="{{ url_for('logout') }}">🚪 Logout</a>
  </div>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
