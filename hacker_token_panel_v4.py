# hacker_token_panel_v4.py
# Premium Hacker Style Token Checker (Harshu Edition)

import requests
from flask import Flask, request, redirect, url_for, session, render_template_string

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------------- CONFIG ----------------
USERNAME = "admin"
PASSWORD = "pass123"

# ---------------- HTML ------------------
LOGIN_HTML = """
<!doctype html>
<html>
<head>
  <title>Harshu Token Checker - Login</title>
  <style>
    body { background-color: black; color: #00ff00; font-family: monospace; }
    .login-box {
      width: 350px;
      margin: 120px auto;
      padding: 20px;
      border: 2px solid #00ff00;
      border-radius: 12px;
      box-shadow: 0 0 20px #00ff00;
      text-align: center;
    }
    h2 {
      color: #00ff00;
      text-shadow: 0 0 10px #00ff00;
      animation: flicker 1.5s infinite alternate;
    }
    @keyframes flicker {
      from { opacity: 1; }
      to { opacity: 0.7; }
    }
    input {
      width: 90%; padding: 10px; margin: 10px 0;
      background: black; border: 1px solid #00ff00;
      color: #00ff00; border-radius: 6px;
    }
    input:focus { outline: none; box-shadow: 0 0 10px #00ff00; }
    button {
      padding: 10px 20px; background: #00ff00; border: none;
      border-radius: 6px; font-weight: bold; cursor: pointer;
      transition: 0.3s;
    }
    button:hover { background: black; color: #00ff00; border: 1px solid #00ff00; }
    footer { margin-top: 15px; font-size: 14px; }
    a { color: #00ff00; text-decoration: none; }
  </style>
</head>
<body>
  <div class="login-box">
    <h2>🔐 Harshu Token Checker Login</h2>
    <form method="post">
      <input type="text" name="username" placeholder="Username"><br>
      <input type="password" name="password" placeholder="Password"><br>
      <button type="submit">Login</button>
    </form>
    <footer>
      Made with 💕 by Harshu<br>
      <a href="https://m.me/harshuuuxd" target="_blank">Contact Me</a>
    </footer>
  </div>
</body>
</html>
"""

DASHBOARD_HTML = """
<!doctype html>
<html>
<head>
  <title>Harshu Token Checker Tool</title>
  <style>
    body { background-color: black; color: #00ff00; font-family: monospace; text-align:center; }
    .banner {
      font-size: 18px; font-weight: bold;
      text-shadow: 0 0 10px #00ff00;
      margin-top: 20px; margin-bottom: 20px;
    }
    .card {
      width: 80%; margin: auto; padding: 20px;
      border: 2px solid #00ff00; border-radius: 12px;
      box-shadow: 0 0 20px #00ff00;
    }
    textarea {
      width: 95%; height: 200px; margin: 10px auto;
      background: black; border: 2px solid #00ff00; border-radius: 8px;
      color: #00ff00; padding: 10px;
    }
    button {
      padding: 10px 20px; margin-top: 10px;
      background: #00ff00; border: none; border-radius: 6px;
      font-weight: bold; cursor: pointer; transition: 0.3s;
    }
    button:hover { background: black; color: #00ff00; border: 1px solid #00ff00; }
    table {
      margin: 20px auto; border-collapse: collapse; width: 80%;
      box-shadow: 0 0 10px #00ff00;
    }
    th, td {
      border: 1px solid #00ff00; padding: 10px;
    }
    tr:nth-child(even) { background: #001a00; }
    tr:hover { background: #003300; }
    footer {
      margin-top: 30px; font-size: 14px;
      border-top: 1px solid #00ff00; padding-top: 10px;
    }
    a { color: #00ff00; text-decoration: none; }
  </style>
</head>
<body>
  <div class="banner">
══════════════════════════════════<br>
     ✦ Harshu Token Checker ✦  <br>
       ⚡ Hatters ki maki chut ☠️⚡<br>
══════════════════════════════════
  </div>

  <div class="card">
    <h2>Paste Tokens Below</h2>
    <form method="post">
      <textarea name="tokens" placeholder="Enter one token per line..."></textarea><br>
      <button type="submit">Check Tokens</button>
    </form>
  </div>

  {% if results %}
  <h2>Results</h2>
  <table>
    <tr><th>Token</th><th>Status</th></tr>
    {% for t, status in results %}
      <tr><td>{{t}}</td><td>{{status}}</td></tr>
    {% endfor %}
  </table>
  {% endif %}

  <footer>
    Made with 💕 by Harshu | <a href="https://m.me/harshuuuxd" target="_blank">Contact Me</a>
  </footer>
</body>
</html>
"""

# ---------------- ROUTES ----------------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")
        if u == USERNAME and p == PASSWORD:
            session["user"] = u
            return redirect(url_for("dashboard"))
    return render_template_string(LOGIN_HTML)

@app.route("/dashboard", methods=["GET","POST"])
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    results = []
    if request.method == "POST":
        tokens = request.form.get("tokens", "").splitlines()
        for t in tokens:
            t = t.strip()
            if not t: continue
            try:
                r = requests.get(f"https://graph.facebook.com/me?access_token={t}", timeout=5)
                if r.status_code == 200 and "id" in r.json():
                    results.append((t[:8]+"..."+t[-6:], "✅ VALID"))
                else:
                    results.append((t[:8]+"..."+t[-6:], "❌ INVALID"))
            except:
                results.append((t[:8]+"..."+t[-6:], "⚠️ ERROR"))

    return render_template_string(DASHBOARD_HTML, results=results)

# ---------------- MAIN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
  
