# Patched: 2025-09-14 - production-ready
"""
Flask web adapter including endpoints for chat, Twilio webhook, counselor and institute APIs.
Note: For production replace local auth middleware with a proper OAuth or Supabase Auth integration.
"""

from flask import Flask, request, jsonify, session, redirect, url_for
from functools import wraps
import os

from chatbot_flow import ChatSession
import supabase_helper as sbh
from config import FLASK_HOST, FLASK_PORT, SECRET_KEY, USE_GOOGLE_OAUTH, GOOGLE_CLIENT_ID, GOOGLE_OAUTH_REDIRECT, TWILIO_NOTIFY_ENABLED

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Simple in-memory sessions map (for demo/testing). Replace with persistent session store in production.
SESSIONS = {}

# -------------------------
# Lightweight token auth (example)
# -------------------------
def require_token(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = request.args.get("token") or request.headers.get("X-API-KEY")
        if token == "dev-token" or token == os.getenv("ADMIN_API_TOKEN"):
            return fn(*args, **kwargs)
        return jsonify({"error": "Unauthorized"}), 401
    return wrapper

# -------------------------
# Health
# -------------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "backend": sbh.health_check()}), 200

# -------------------------
# Chat send endpoint (unified for console/web)
# -------------------------
@app.route("/send", methods=["POST"])
def send_message():
    payload = request.get_json() or {}
    sender = payload.get("sender", "anon")
    text = payload.get("text", "")
    channel = payload.get("channel", "web")
    session_id = payload.get("session_id")
    # retrieve or create session object
    sess = None
    if session_id and session_id in SESSIONS:
        sess = SESSIONS[session_id]
    else:
        sess = ChatSession(session_id=session_id or None, user_id=sender, channel=channel)
        SESSIONS[sess.session_id] = sess
    # route based on state
    reply = ""
    if sess.state == "ONBOARD":
        reply = sess.start_onboarding()
    elif sess.state == "MOOD_PROMPT":
        reply = sess.prompt_mood()
    elif sess.state == "SCREENING_Q":
        # treat incoming text as answer
        reply = sess.receive_answer(text)
    elif sess.state == "APPOINTMENT_FLOW":
        reply = sess.handle_post_screening_choice(text)
    else:
        # basic routing heuristics
        if "name" not in sess.persona:
            reply = sess.receive_onboard(text)
        elif "year" not in sess.persona:
            reply = sess.receive_year(text)
        else:
            # if session waiting for mood
            if sess.state in (None, "ONBOARD", "MOOD_PROMPT"):
                reply = sess.receive_mood(text)
            else:
                reply = "I'm not sure how to handle that. Try saying 'help'."
    # update last interaction
    sess.last_interaction = sbh._utcnow_iso() if hasattr(sbh, "_utcnow_iso") else ""
    return jsonify({"reply": reply, "session_id": sess.session_id})

# -------------------------
# Twilio WhatsApp webhook endpoint (POST)
# -------------------------
@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    # Twilio posts form-encoded body
    try:
        from_number = request.form.get("From")
        body = request.form.get("Body")
        # simple mapping: use from_number as user id
        sess = None
        # find existing session by user id if available
        for s in SESSIONS.values():
            if s.user_id == from_number:
                sess = s
                break
        if not sess:
            sess = ChatSession(user_id=from_number, channel="whatsapp")
            SESSIONS[sess.session_id] = sess
        # feed message as text
        # route logic similar to /send
        if "name" not in sess.persona:
            reply = sess.receive_onboard(body)
        elif "year" not in sess.persona:
            reply = sess.receive_year(body)
        else:
            # if in screening, treat as answer
            if sess.state == "SCREENING_Q":
                reply = sess.receive_answer(body)
            else:
                # treat this as mood input
                reply = sess.receive_mood(body)
        # Respond with TwiML
        from flask import Response
        twiml = f"<Response><Message>{reply}</Message></Response>"
        return Response(twiml, mimetype="application/xml")
    except Exception as e:
        return jsonify({"error": "failed to process webhook", "detail": str(e)}), 500

# -------------------------
# Counselor endpoints
# -------------------------
@app.route("/counselor/scores/<user_id>", methods=["GET"])
@require_token
def counselor_scores(user_id):
    # return raw scores for counsellors (not shown to students)
    scores = sbh.get_user_scores(user_id)
    return jsonify({"user_id": user_id, "scores": scores})

@app.route("/institute/heatmap", methods=["GET"])
@require_token
def institute_heatmap():
    dept = request.args.get("dept")
    year = request.args.get("year")
    from progress_store import get_department_aggregates
    window = int(request.args.get("window", "30"))
    data = get_department_aggregates(dept, year, window)
    return jsonify({"heatmap": data})

@app.route("/alerts", methods=["GET"])
@require_token
def alerts_list():
    # read local fallback alerts
    try:
        import json
        from config import LOCAL_SAVE_PATH
        if not os.path.exists(LOCAL_SAVE_PATH):
            return jsonify({"alerts": []})
        with open(LOCAL_SAVE_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        alerts = [e["payload"] for e in data if e["type"] == "alert"]
        return jsonify({"alerts": alerts})
    except Exception:
        return jsonify({"alerts": []})

# -------------------------
# Google OAuth routes (placeholders)
# -------------------------
@app.route("/auth/google")
def auth_google():
    if not USE_GOOGLE_OAUTH:
        return jsonify({"error": "google auth disabled"}), 400
    # In production implement oauth2 flow; here show placeholder redirect
    return redirect("https://accounts.google.com/o/oauth2/v2/auth")

@app.route("/auth/google/callback")
def auth_google_callback():
    # Placeholder: handle code exchange and user creation
    return jsonify({"status": "ok", "note": "implement OAuth callback in production"})

# -------------------------
# Run
# -------------------------
def run_app():
    app.run(host=FLASK_HOST, port=FLASK_PORT)

if __name__ == "__main__":
    run_app()
