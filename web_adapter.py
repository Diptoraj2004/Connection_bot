# web_adapter.py
from flask import Flask, render_template_string, request, redirect, url_for, session
from supabase_helper import get_sb_client
from progress_store import load_user_state
import os, json

app = Flask(__name__)
app.secret_key = "supersecretkey"  # required for session management

# ---------------------------
# Base Styles
# ---------------------------
BASE_STYLE = """
  body { font-family: Arial, sans-serif; margin: 2em; }
  table { border-collapse: collapse; width: 100%; margin-top: 1em; }
  th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
  th { background: #eee; }
  a { text-decoration: none; color: #0066cc; }
  input, select { padding: 5px; margin: 5px 0; }
"""

# ---------------------------
# Templates
# ---------------------------
LOGIN_TEMPLATE = f"""
<!doctype html>
<html>
  <head><title>Login</title></head>
  <body style="{BASE_STYLE}">
    <h1>🔑 Login</h1>
    <form method="POST">
      <label>User ID:</label><br>
      <input type="text" name="user_id" required><br>
      <label>Role:</label><br>
      <select name="role">
        <option value="student">Student</option>
        <option value="counselor">Counselor</option>
        <option value="institution">Institution</option>
      </select><br>
      <button type="submit">Login</button>
    </form>
    {{% if error %}}<p style="color:red;">{{{{ error }}}}</p>{{% endif %}}
  </body>
</html>
"""

INDEX_TEMPLATE = f"""
<!doctype html>
<html>
  <head><title>Mental Health Platform</title></head>
  <body style="{BASE_STYLE}">
    <h1>🌱 Mental Health Platform</h1>
    <p>Welcome, {{{{ session.get('user_id') }}}} ({ {{{{ session.get('role') }}}} })</p>
    <ul>
      <li><a href='/dashboard/student'>Student Dashboard</a></li>
      <li><a href='/dashboard/counselor'>Counselor Dashboard</a></li>
      <li><a href='/dashboard/institution'>Institution Dashboard</a></li>
      <li><a href='/logout'>Logout</a></li>
    </ul>
  </body>
</html>
"""

COUNSELOR_TEMPLATE = f"""
<!doctype html>
<html>
  <head><title>Counselor Dashboard</title></head>
  <body style="{BASE_STYLE}">
    <h1>📊 Counselor Dashboard</h1>
    <p>Escalation Logs (latest first)</p>
    <table>
      <tr><th>User</th><th>Reason</th><th>Timestamp</th></tr>
      {{% for row in logs %}}
        <tr>
          <td>{{{{ row.user_id }}}}</td>
          <td>{{{{ row.reason }}}}</td>
          <td>{{{{ row.ts }}}}</td>
        </tr>
      {{% endfor %}}
    </table>
    {{% if not logs %}}
      <p><i>No escalation logs available.</i></p>
    {{% endif %}}
    <p><a href='/'>Back to Home</a></p>
  </body>
</html>
"""

STUDENT_TEMPLATE = f"""
<!doctype html>
<html>
  <head><title>Student Dashboard</title></head>
  <body style="{BASE_STYLE}">
    <h1>🎓 Student Dashboard</h1>
    <p>Feature under construction...</p>
    <p><a href='/'>Back to Home</a></p>
  </body>
</html>
"""

INSTITUTION_TEMPLATE = f"""
<!doctype html>
<html>
  <head><title>Institution Dashboard</title></head>
  <body style="{BASE_STYLE}">
    <h1>🏢 Institution Dashboard</h1>
    <p>Aggregated Analytics (placeholder)</p>
    <p><a href='/'>Back to Home</a></p>
  </body>
</html>
"""

# ---------------------------
# Helpers
# ---------------------------
def fetch_escalations():
    """Fetch escalation logs from Supabase or fallback to local JSON."""
    logs = []
    try:
        sb = get_sb_client()
        res = sb.table("escalations").select("*").order("ts", desc=True).execute()
        if res.data:
            logs = res.data
    except Exception as e:
        print("⚠️ Supabase unavailable, falling back:", e)
        if os.path.exists("local_progress.json"):
            data = json.load(open("local_progress.json"))
            for uid, state in data.items():
                for esc in state.get("escalation_log", []):
                    logs.append({
                        "user_id": uid,
                        "reason": esc.get("reason", ""),
                        "ts": esc.get("ts", "")
                    })
    return logs

def save_first_time_user(user_id, role):
    """Save first-time user locally."""
    data = {}
    if os.path.exists("local_progress.json"):
        data = json.load(open("local_progress.json"))
    if user_id not in data:
        data[user_id] = {
            "role": role,
            "mood_log": [],
            "sleep_log": [],
            "streak": 0,
            "escalation_log": []
        }
        json.dump(data, open("local_progress.json", "w"), indent=2)

# ---------------------------
# Routes
# ---------------------------
@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template_string(INDEX_TEMPLATE)

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        user_id = request.form.get("user_id")
        role = request.form.get("role")
        if not user_id or not role:
            error = "Please enter both user ID and role."
        else:
            # save first-time users
            save_first_time_user(user_id, role)
            session["user_id"] = user_id
            session["role"] = role
            # redirect based on role
            if role == "student":
                return redirect(url_for("student_dashboard"))
            elif role == "counselor":
                return redirect(url_for("counselor_dashboard"))
            elif role == "institution":
                return redirect(url_for("institution_dashboard"))
            else:
                error = "Invalid role selected."
    return render_template_string(LOGIN_TEMPLATE, error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard/counselor")
def counselor_dashboard():
    if session.get("role") != "counselor":
        return redirect(url_for("login"))
    logs = fetch_escalations()
    return render_template_string(COUNSELOR_TEMPLATE, logs=logs)

@app.route("/dashboard/student")
def student_dashboard():
    if session.get("role") != "student":
        return redirect(url_for("login"))
    return render_template_string(STUDENT_TEMPLATE)

@app.route("/dashboard/institution")
def institution_dashboard():
    if session.get("role") != "institution":
        return redirect(url_for("login"))
    return render_template_string(INSTITUTION_TEMPLATE)

# ---------------------------
# Run App
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)
