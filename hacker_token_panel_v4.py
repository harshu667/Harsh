from flask import Flask, render_template_string, request, redirect, url_for, session
import requests

app = Flask(__name__)
app.secret_key = "harshu_secret"

USERNAME = "admin"
PASSWORD = "password"

# ----------------- LOGIN PAGE -----------------
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Login</title>
  <style>
    body {
      margin:0;
      background:black;
      color:#00ffcc;
      font-family: 'Poppins', monospace;
      display:flex;
      justify-content:center;
      align-items:center;
      height:100vh;
    }
    .login-box {
      background: rgba(255,255,255,0.05);
      padding:30px;
      border-radius:16px;
      border:1px solid #00ffcc;
      backdrop-filter: blur(10px);
      text-align:center;
      width:320px;
    }
    h2 {
      margin:0 0 20px;
      font-size:22px;
      background: linear-gradient(90deg, #ff00cc, #00ffff);
      -webkit-background-clip: text;
      color: transparent;
      text-shadow: 0 0 15px #ff00cc;
    }
    input {
      width:100%;
      padding:12px;
      margin:8px 0;
      border:none;
      border-radius:8px;
      background:#0a0a0a;
      color:#00ffcc;
      border:1px solid #00ffcc;
    }
    button {
      width:100%;
      padding:12px;
      margin-top:12px;
      background: linear-gradient(90deg,#ff00cc,#00ffff);
      border:none;
      color:white;
      font-weight:bold;
      border-radius:10px;
      cursor:pointer;
      transition:0.3s;
    }
    button:hover { transform: scale(1.05); box-shadow:0 0 20px #ff00cc; }
    .footer {
      margin-top:15px;
      font-size:13px;
      color:#00ffcc;
    }
    .footer span {
      background: linear-gradient(90deg,#ff00cc,#00ffff);
      -webkit-background-clip: text;
      color: transparent;
      font-weight:bold;
    }
    .footer a {
      color:#00ffff;
      text-decoration:none;
      font-weight:bold;
    }
  </style>
</head>
<body>
  <div class="login-box">
    <h2>Login to continue</h2>
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

# ----------------- DASHBOARD PAGE -----------------
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>{{title}} - Dashboard</title>
  <style>
    body {
      margin:0;
      background:black;
      color:#00ffcc;
      font-family: 'Poppins', monospace;
      display:flex;
      flex-direction:column;
      min-height:100vh;
    }
    .container {
      flex:1;
      display:flex;
      flex-direction:column;
      align-items:center;
      padding:20px;
    }
    .banner { text-align:center; margin-bottom:20px; }
    .banner .title {
      font-size: 34px;
      font-weight: bold;
      background: linear-gradient(90deg, #ff00cc, #00ffff);
      -webkit-background-clip: text;
      color: transparent;
      text-shadow: 0 0 25px #ff00cc;
      margin: 0;
    }
    .banner .subtitle {
      font-size: 20px;
      font-weight: 600;
      color: #ff0066;
      text-shadow: 0 0 15px #ff0066, 0 0 30px #ff00cc;
      margin-top: 10px;
    }
    textarea {
      width:90%;
      max-width:700px;
      height:120px;
      background:#0a0a0a;
      color:#00ffcc;
      border:2px solid #00ffcc;
      border-radius:10px;
      padding:12px;
      font-size:14px;
      margin-top:10px;
    }
    button {
      background: linear-gradient(90deg,#ff00cc,#00ffff);
      border:none;
      padding:12px 24px;
      margin-top:15px;
      color:white;
      font-weight:bold;
      cursor:pointer;
      border-radius:10px;
      transition:0.3s;
    }
    button:hover { transform: scale(1.05); box-shadow:0 0 20px #ff00cc; }
    .summary {
      margin:25px auto;
      padding:20px;
      border-radius:16px;
      background: linear-gradient(135deg, rgba(255,0,200,0.15), rgba(0,255,200,0.15));
      border:1px solid #00ffcc;
      width:80%;
      max-width:600px;
      text-align:center;
      box-shadow: 0 0 25px rgba(0,255,200,0.3);
    }
    .cards {
      display:flex;
      flex-wrap:wrap;
      justify-content:center;
      gap:15px;
      margin-top:20px;
      width:100%;
      max-width:950px;
    }
    .card {
      flex:1 1 calc(45% - 20px);
      min-width:280px;
      background: rgba(255,255,255,0.05);
      backdrop-filter: blur(10px);
      border:1px solid #00ffcc;
      border-radius:12px;
      padding:15px;
      box-shadow:0 0 15px rgba(0,255,200,0.3);
      color:#fff;
    }
    .card h3 {
      margin:0;
      font-size:16px;
      color:#00ffff;
      word-break:break-all;
    }
    .status {
      margin-top:8px;
      font-weight:bold;
      padding:6px 10px;
      border-radius:8px;
      display:inline-block;
    }
    .valid { background:rgba(0,255,100,0.2); color:#00ff88; border:1px solid #00ff88; }
    .invalid { background:rgba(255,0,100,0.2); color:#ff0055; border:1px solid #ff0055; }
    .error { background:rgba(255,200,0,0.2); color:#ffcc00; border:1px solid #ffcc00; }
    .footer {
      text-align:center;
      padding:15px;
      font-size:14px;
      color:#00ffcc;
      border-top:1px solid #00ffcc;
      display:flex;
      justify-content:space-between;
      align-items:center;
    }
    .footer span {
      background: linear-gradient(90deg,#ff00cc,#00ffff);
      -webkit-background-clip: text;
      color: transparent;
      font-weight:bold;
    }
    .footer a {
      color:#00ffff;
      text-decoration:none;
      font-weight:bold;
    }
    .logout {
      background:#ff0066;
      padding:8px 16px;
      border-radius:8px;
      color:white;
      font-weight:bold;
      text-decoration:none;
      transition:0.3s;
    }
    .logout:hover {
      background:#ff0033;
      box-shadow:0 0 15px #ff0055;
    }
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
      <h1 class="title">✨ Harshu Token Checker ✨</h1>
      <h2 class="subtitle">⚡ Hatters ki maki chut ☠️⚡</h2>
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

    <div class="cards">
      {% for r in results %}
        <div class="card">
          <h3>{{r.token}}</h3>
          {% if r.status == 'valid' %}
            <div class="status valid">✅ Valid</div>
          {% elif r.status == 'invalid' %}
            <div class="status invalid">❌ Invalid</div>
          {% else %}
            <div class="status error">⚠️ Error</div>
          {% endif %}
          <p><b>User ID:</b> {{r.id if r.id else '-'}}</p>
          <p><b>Name:</b> {{r.name if r.name else '-'}}</p>
        </div>
      {% endfor %}
    </div>
    {% endif %}
  </div>

  <div class="footer">
    <div>
      Made with ❤️ by <span>Harshu</span><br>
      <a href="https://m.me/harshuuuxd" target="_blank">📩 Contact Me</a>
    </div>
    <a class="logout" href="{{ url_for('logout') }}">🚪 Logout</a>
  </div>
</body>
</html>
"""

# ----------------- FLASK ROUTES -----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == USERNAME and request.form["password"] == PASSWORD:
            session["user"] = USERNAME
            return redirect(url_for("dashboard"))
    return render_template_string(LOGIN_HTML)

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session: return redirect(url_for("login"))
    results, summary, alive_tokens = [], None, []
    if request.method == "POST":
        tokens = request.form["tokens"].splitlines()
        total, active, dead, error = 0,0,0,0
        for token in tokens:
            token = token.strip()
            if not token: continue
            total+=1
            try:
                r = requests.get("https://graph.facebook.com/me?access_token="+token,timeout=5)
                if r.status_code==200:
                    data=r.json()
                    results.append({"token":token,"status":"valid","id":data.get("id"),"name":data.get("name")})
                    active+=1; alive_tokens.append(token)
                else:
                    results.append({"token":token,"status":"invalid","id":None,"name":None})
                    dead+=1
            except Exception:
                results.append({"token":token,"status":"error","id":None,"name":None})
                error+=1
        summary={"total":total,"active":active,"dead":dead,"error":error}
    return render_template_string(DASHBOARD_HTML,title="Harshu Panel",results=results,summary=summary,alive_tokens=alive_tokens)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
    
