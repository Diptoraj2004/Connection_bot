# Patched: 2025-10-12 - Unified Flask API for Crusade Codex backend
"""
Unified API backend connecting chatbot_flow, Supabase, and local fallback.
"""

from flask import Flask, request, jsonify
from datetime import datetime
import traceback

import chatbot_flow
import supabase_helper as sbh
import data_loader
import emergency

app = Flask(__name__)

@app.route("/health")
def health():
    """Simple health check"""
    return jsonify({
        "status": "ok",
        "time": datetime.utcnow().isoformat(),
        "modules": {
            "chatbot_flow": hasattr(chatbot_flow, "handle_incoming_message"),
            "supabase": hasattr(sbh, "upsert_response"),
            "data_loader": hasattr(data_loader, "load_all_datasets")
        }
    })


# -----------------------------
# Chatbot unified endpoints
# -----------------------------

@app.route("/api/chat/start", methods=["POST"])
def start_chat():
    """
    Start a chat session for a user.
    Body: { "user_id": "abc", "channel": "web" }
    """
    data = request.json or {}
    user_id = data.get("user_id", "guest")
    sb = sbh.get_sb_client()
    msg = chatbot_flow.handle_incoming_message(sb, user_id, "Hello")
    return jsonify({"reply": msg})


@app.route("/api/chat/message", methods=["POST"])
def chat_message():
    """
    Continue conversation with chatbot.
    Body: { "user_id": "abc", "message": "I feel sad" }
    """
    data = request.json or {}
    user_id = data.get("user_id", "guest")
    text = data.get("message", "")
    try:
        sb = sbh.get_sb_client()
        reply = chatbot_flow.handle_incoming_message(sb, user_id, text)
        return jsonify({"reply": reply})
    except Exception as e:
        print("Chat error:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# -----------------------------
# Questionnaire & Data
# -----------------------------

@app.route("/api/questionnaires", methods=["GET"])
def list_questionnaires():
    """List all available screening tools"""
    datasets = data_loader.load_all_datasets()
    return jsonify({"available": list(datasets.keys())})


@app.route("/api/questionnaire/<name>", methods=["GET"])
def get_questionnaire(name):
    """Fetch questions for a given tool"""
    datasets = data_loader.load_all_datasets()
    qset = datasets.get(name.upper()) or datasets.get(name.title()) or []
    return jsonify({"name": name, "questions": qset})


# -----------------------------
# Emergency endpoint
# -----------------------------

@app.route("/api/emergency/check", methods=["POST"])
def check_emergency():
    """
    Check a message for emergency keywords.
    Body: { "user_id": "...", "message": "..." }
    """
    data = request.json or {}
    msg = data.get("message", "")
    resp = emergency.check_emergency(msg)
    if resp:
        emergency.trigger_emergency_escalation(data.get("user_id", "guest"), msg)
        return jsonify({"escalated": True, "message": resp})
    return jsonify({"escalated": False})


# -----------------------------
# IoT placeholder
# -----------------------------
@app.route("/api/iot/upload", methods=["POST"])
def iot_upload():
    """
    Placeholder IoT ingestion.
    Body: { "user_id": "...", "metrics": {...} }
    """
    data = request.json or {}
    user_id = data.get("user_id", "guest")
    metrics = data.get("metrics", {})
    try:
        sbh.insert_iot_reading(user_id, metrics)
        return jsonify({"status": "saved"})
    except Exception as e:
        print("IoT upload error:", e)
        return jsonify({"error": str(e)}), 500


# -----------------------------
# Run server
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
