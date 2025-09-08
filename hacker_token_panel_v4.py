# hacker_token_panel_v6.py
# Ultra Premium Rainbow Wave Token Checker with Animated Borders

import requests
from flask import Flask, request, session, redirect, url_for, render_template_string

APP_TITLE = "Harshu Token Checker Tool"
USERS = {"Harshu00": "Harshu_don"}

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Utils
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

# -------- HTML with Rainbow Borders --------
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>{{title}} - Login</title>
  <style>
    @keyframes rainbow {0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
    @keyframes borderGlow {0%{border-image-source:linear-gradient(270deg,#ff00cc,#00ffff,#ff9900,#33ff00,#ff0000,#6600ff);}50%{border-image-source:linear-gradient(270deg,#6600ff,#ff0000,#33ff00,#ff9900,#00ffff,#ff00cc);}100%{border-image-source:linear-gradient(270deg,#ff00cc,#00ffff,#ff9900,#33ff00,#ff0000,#6600ff);}}

    body {
      margin:0; height:100vh; display:flex; justify-content:center; align-items:center;
      background:linear-gradient(270deg,#ff00cc,#00ffff,#ff9900,#33ff00,#ff0000,#6600ff);
      background-size:1200% 1200%; animation:rainbow 20s ease infinite;
      font-family:'Poppins',sans-serif; color:white;
    }
    .login-box {
      background:rgba(0,0,0,0.6); backdrop-filter:blur(14px);
      border-radius:25px; padding:50px 35px; text-align:center; width:400px;
      box-shadow:0 0 40px rgba(255,255,255,0.5);
      border:6px solid transparent; border-image-slice:1;
      animation:borderGlow 8s linear infinite;
    }
    h1 {font-size:36px;margin-bottom:10px;font-weight:800;background:linear-gradient(90deg,#ff00cc,#00ffff,#ff9900);
      -webkit-background-clip:text;color:transparent;text-shadow:0 0 25px #00ffff;}
    h3 {margin-bottom:30px;font-weight:500;color:#eee;}
    input {width:100%;padding:15px;margin:12px 0;border:none;border-radius:15px;outline:none;
      background:rgba(255,255,255,0.1);color:#fff;font-size:16px;border:2px solid transparent;border-image-slice:1;
      animation:borderGlow 6s linear infinite;}
    input:focus {box-shadow:0 0 15px #00ffff;}
    button {width:100%;padding:15px;margin-top:20px;background:linear-gradient(90deg,#ff00cc,#00ffff,#ff9900);
      border:none;border-radius:15px;color:white;font-weight:bold;font-size:18px;cursor:pointer;
      box-shadow:0 0 15px #00ffff;transition:0.3s;}
    button:hover {transform:scale(1.08);box-shadow:0 0 30px #ff00cc,0 0 30px #00ffff;}
    .footer {margin-top:22px;font-size:15px;color:#ddd;}
    .footer span {background:linear-gradient(90deg,#ff00cc,#00ffff);-webkit-background-clip:text;color:transparent;font-weight:bold;}
  </style>
</head>
<body>
  <div class="login-box">
    <h1>HARSHU TOOL</h1>
    <h3>Login to continue</h3>
    {% if error %}<p style="color:red">{{error}}</p>{% endif %}
    <form method="post">
      <input type="text" name="username" placeholder="Username" required>
      <input type="password" name="password" placeholder="Password" required>
      <button type="submit">Login</button>
    </form>
    <div class="footer">Made with ❤️ by <span>Harshu</span></div>
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
    @keyframes rainbow {0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
    @keyframes borderGlow {0%{border-image-source:linear-gradient(270deg,#ff00cc,#00ffff,#ff9900,#33ff00,#ff0000,#6600ff);}50%{border-image-source:linear-gradient(270deg,#6600ff,#ff0000,#33ff00,#ff9900,#00ffff,#ff00cc);}100%{border-image-source:linear-gradient(270deg,#ff00cc,#00ffff,#ff9900,#33ff00,#ff0000,#6600ff);}}

    body {margin:0;background:linear-gradient(270deg,#ff00cc,#00ffff,#ff9900,#33ff00,#ff0000,#6600ff);
      background-size:1200% 1200%;animation:rainbow 25s ease infinite;color:#00ffcc;font-family:monospace;
      display:flex;flex-direction:column;min-height:100vh;}
    .container {flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-start;padding:25px;}
    .banner {text-align:center;font-size:32px;font-weight:bold;margin-bottom:30px;color:#fff;
      text-shadow:0 0 20px #00ffff,0 0 30px #ff00ff;}
    textarea {width:95%;max-width:850px;height:200px;background:rgba(0,0,0,0.6);color:#00ffcc;
      border:6px solid transparent;border-image-slice:1;animation:borderGlow 10s linear infinite;
      border-radius:15px;padding:18px;font-size:16px;backdrop-filter:blur(10px);}
    button {background:linear-gradient(90deg,#ff00cc,#00ffff,#ff9900);border:none;padding:15px 30px;
      margin-top:20px;color:white;font-weight:bold;cursor:pointer;border-radius:12px;font-size:18px;
      box-shadow:0 0 15px #00ffff;transition:0.3s;}
    button:hover {box-shadow:0 0 30px #ff00cc,0 0 30px #00ffff;transform:scale(1.08);}
    .card {background:rgba(255,255,255,0.08);border:4px solid transparent;border-image-slice:1;
      animation:borderGlow 12s linear infinite;border-radius:18px;padding:18px;margin:15px auto;
      width:95%;max-width:850px;box-shadow:0 0 20px #00ffff;font-size:16px;color:#fff;}
    .summary {margin:30px auto;padding:25px;border:4px solid transparent;border-image-slice:1;
      animation:borderGlow 8s linear infinite;border-radius:18px;width:80%;max-width:650px;
      background:rgba(0,0,0,0.6);backdrop-filter:blur(12px);box-shadow:0 0 30px rgba(0,255,255,0.6);
      text-align:center;font-size:17px;color:#fff;}
    .footer {text-align:center;padding:25px;font-size:17px;color:#fff;border-top:2px solid rgba(255,255,255,0.3);
      margin-top:35px;backdrop-filter:blur(8px);background:rgba(0,0,0,0.5);}
    .footer a {display:inline-block;margin:0 12px;padding:12px 22px;border-radius:10px;
      background:linear-gradient(90deg,#ff00cc,#00ffff,#ff9900);color:white;font-weight:bold;text-decoration:none;
      box-shadow:0 0 18px #00ffff;transition:0.3s;}
    .footer a:hover {box-shadow:0 0 30px #ff00cc,0 0 30px #00ffff;transform:scale(1.08);}
  </style>
</head>
<body>
  <div class="container">
    <div class="banner">✦ Harshu Token Checker ✦<br><span style="color:#ffea00;">🌈 Rainbow Premium Panel 🌈</span></div>
    <form method="post">
      <textarea name="tokens" placeholder="Enter tokens here (one per line)..."></textarea><br>
      <button type="submit">🚀 Check Tokens</button>
    </form>
    {% if summary %}
    <div class="summary">
      <b>Total:</b> {{summary.total}} | ✅ Active: {{summary.active}} | ❌ Dead: {{summary.dead}} | ⚠️ Errors: {{summary.error}}
      {% if summary.active > 0 %}
        <br><br><button onclick="copyAlive()">📋 Copy Alive Tokens</button>
        <textarea id="aliveTokens" style="display:none;">{% for t in alive_tokens %}{{t}}&#10;{% endfor %}</textarea>
      {% endif %}
    </div>
    {% for r in results %}
      <div class="card"><b>🔑 Token:</b> {{r.token}} <br>
      <b>Status:</b> {% if r.status == 'valid' %}✅ Valid{% elif r.status == 'invalid' %}❌ Invalid{% else %}⚠️ Error{% endif %}<br>
      <b>User ID:</b> {{r.id if r.id else '-'}} <br><b>Name:</b> {{r.name if r.name else '-' }}</div>
    {% endfor %}
    {% endif %}
  </div>
  <div class="footer">Made with ❤️ by Harshu <br><br>
    <a href="https://m.me/harshuuuxd" target="_blank">📩 Contact Me</a>
    <a href="{{ url_for('logout') }}">🚪 Logout</a>
  </div>
  <script>
    function copyAlive(){
      var txt=document.getElementById("aliveTokens");txt.style.display="block";txt.select();
      document.execCommand("copy");txt.style.display="none";alert("✅ Alive tokens copied!");
    }
  </script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
