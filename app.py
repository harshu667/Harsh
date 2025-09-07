from flask import Flask, render_template_string, request, session, redirect, url_for
import requests, json, os

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "harshu_secret_key")

# Default users (can override with USERS_JSON env var)
USERS = {"admin": "pass123", "harshu": "1234"}
if os.getenv("USERS_JSON"):
    try:
        USERS.update(json.loads(os.getenv("USERS_JSON")))
    except:
        pass

# In-memory history
HISTORY = {}

# HTML Template (inline)
TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>Harshu Token Checker Tool</title>
  <style>
    body {
      background: #0d0d0d;
      color: #00ffcc;
      font-family: monospace;
      text-align: center;
    }
    h1 {
      font-size: 28px;
      color: #0ff;
      text-shadow: 0 0 10px #0ff, 0 0 20px #00cccc;
    }
    pre.banner {
      font-size: 16px;
      color: #00ff99;
      text-shadow: 0 0 10px #00ff99, 0 0 20px #00cc88;
    }
    .box {
      background: #111;
      padding: 20px;
      margin: 20px auto;
      border-radius: 12px;
      width: 80%%;
      box-shadow: 0 0 15px #0ff;
    }
    textarea {
      width: 90%%;
      height: 150px;
      background: #000;
      color: #0f0;
      border: 1px solid #0ff;
      padding: 10px;
    }
    button {
      background: #0ff;
      color: #000;
      font-weight: bold;
      padding: 10px 20px;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      margin-top: 10px;
      transition: all 0.2s;
    }
    button:hover {
      background: #00ccaa;
      box-shadow: 0 0 10px #00ffcc;
    }
    table {
      width: 100%%;
      border-collapse: collapse;
      margin-top: 20px;
    }
    th, td {
      border: 1px solid #0ff;
      padding: 8px;
    }
    th {
      background: #111;
      color: #0ff;
    }
    td.valid {
      color: #0f0;
      text-shadow: 0 0 5px #0f0;
    }
    td.invalid {
      color: #f33;
      text-shadow: 0 0 5px #f33;
    }
    footer {
      margin-top: 40px;
      font-size: 14px;
      color: #999;
    }
    footer a {
      color: #0ff;
      text-decoration: none;
    }
    footer a:hover {
      text-shadow: 0 0 10px #0ff;
    }
  </style>
</head>
<body>
  <h1>HARSHU TOKEN CHECKER TOOL</h1>
  <pre class="banner">
══════════════════════════════════
     ✦ Harshu Token Checker ✦
     ⚡ Hatters ki maki chut ☠️ ⚡
══════════════════════════════════
  </pre>

  {% if not session.get('user') %}
  <div class="box">
    <h2>Login to Continue</h2>
    <form method="post" action="{{ url_for('login') }}">
      <input name="username" placeholder="Username" required><br><br>
      <input type="password" name="password" placeholder="Password" required><br><br>
      <button type="submit">Login</button>
    </form>
  </div>
  {% else %}
  <div class="box">
    <h2>Enter Tokens (one per line)</h2>
    <form method="post" action="{{ url_for('check') }}">
      <textarea name="tokens" required></textarea><br>
      <button type="submit">Check Tokens</button>
    </form>
  </div>

  {% if results %}
  <div class="box">
    <h2>Results</h2>
    <table>
      <tr><th>Token</th><th>Status</th><th>User</th></tr>
      {% for r in results %}
        <tr>
          <td>{{ r.token[:25] }}...</td>
          {% if r.valid %}
            <td class="valid">✅ VALID</td>
            <td class="valid">{{ r.user }}</td>
          {% else %}
            <td class="invalid">❌ INVALID</td>
            <td class="invalid">-</td>
          {% endif %}
        </tr>
      {% endfor %}
    </table>
  </div>
  {% endif %}

  <div class="box">
    <h2>History</h2>
    {% if history %}
      <ul>
      {% for h in history %}
        <li>{{ h }}</li>
      {% endfor %}
      </ul>
    {% else %}
      <p>No history yet.</p>
    {% endif %}
  </div>

  <form method="post" action="{{ url_for('logout') }}">
    <button type="submit">Logout</button>
  </form>
  {% endif %}

  <footer>
    Made with 💕 by Harshu | <a href="https://m.me/harshuuuxd" target="_blank">Contact Me</a>
  </footer>
</body>
</html>
"""

# Routes
@app.route("/", methods=["GET"])
def home():
    if not session.get("user"):
        return render_template_string(TEMPLATE)
    return render_template_string(TEMPLATE, results=None, history=HISTORY.get(session["user"], []))

@app.route("/login", methods=["POST"])
def login():
    u, p = request.form.get("username"), request.form.get("password")
    if USERS.get(u) == p:
        session["user"] = u
        HISTORY.setdefault(u, [])
        return redirect(url_for("home"))
    return "Invalid credentials. <a href='/'>Try again</a>"

@app.route("/logout", methods=["POST"])
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))

@app.route("/check", methods=["POST"])
def check():
    if not session.get("user"):
        return redirect(url_for("home"))
    tokens = request.form.get("tokens", "").splitlines()
    results = []
    for t in tokens:
        t = t.strip()
        if not t: continue
        res = {"token": t, "valid": False, "user": None}
        try:
            r = requests.get(f"https://graph.facebook.com/me?fields=id,name&access_token={t}", timeout=5).json()
            if "id" in r:
                res["valid"] = True
                res["user"] = f"{r.get('name')} ({r.get('id')})"
        except:
            pass
        results.append(res)
    HISTORY[session["user"]].append(f"Checked {len(results)} tokens")
    return render_template_string(TEMPLATE, results=results, history=HISTORY.get(session["user"], []))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
