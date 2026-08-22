"""
colab_runner.py — SentinelMind v5 Colab Launcher.

Paste entire file as ONE cell. Server runs in background thread.
Auto-detects folder. Supports Mode 1 (testing) and Mode 2 (business).
"""

# ══════════════════════════════════════════════════════════════════════════════
# EDIT HERE ONLY
# ══════════════════════════════════════════════════════════════════════════════
GROQ_API_KEY          = "gsk_YOUR_KEY_HERE"       # console.groq.com — free
NGROK_AUTH_TOKEN      = "YOUR_NGROK_TOKEN_HERE"   # dashboard.ngrok.com — free
APP_MODE              = 1    # 1=Testing (JSON DB, sandbox) | 2=Business (Supabase, real Twilio)

# Mode 1 credentials (free, sandbox)
TWILIO_ACCOUNT_SID    = ""   # twilio.com — free sandbox
TWILIO_AUTH_TOKEN_VAL = ""
TWILIO_WHATSAPP_FROM  = "whatsapp:+14155238886"   # Twilio sandbox number

# Mode 2 credentials (free tiers, real services)
SUPABASE_URL          = ""   # supabase.com — free 500MB
SUPABASE_KEY          = ""
REDIS_URL             = ""   # upstash.com — free 10K req/day
FITBIT_CLIENT_ID      = ""   # dev.fitbit.com — free
FITBIT_CLIENT_SECRET  = ""
GOOGLE_FIT_CLIENT_ID  = ""   # console.cloud.google.com — free tier
GOOGLE_FIT_SECRET     = ""

# Optional for both modes
KAGGLE_USERNAME       = ""
KAGGLE_KEY            = ""
TRAIN_ML              = True
USE_KAGGLE_DATA       = True
INSTALL_WHISPER       = True
INSTALL_MEDIAPIPE     = False  # Camera analysis — adds ~500MB
INSTALL_LIBROSA       = False  # Voice prosody — adds ~200MB

# ══════════════════════════════════════════════════════════════════════════════
# STEP 1: FIND PROJECT
# ══════════════════════════════════════════════════════════════════════════════
import os, sys, subprocess, glob

def find_root() -> str:
    for candidate in (glob.glob("/content/sentinelmind*/") +
                      glob.glob("/content/*/main.py") +
                      glob.glob("/root/sentinelmind*/")):
        root = candidate if os.path.isdir(candidate) else os.path.dirname(candidate)
        if os.path.exists(os.path.join(root, "main.py")):
            return root
    for dp, _, fs in os.walk("/content"):
        if "main.py" in fs and "config.py" in fs:
            return dp
    raise RuntimeError("Cannot find sentinelmind project. Unzip first.")

ROOT = find_root()
print(f"✅ Project: {ROOT}")
sys.path.insert(0, ROOT)
os.chdir(ROOT)

# ══════════════════════════════════════════════════════════════════════════════
# STEP 2: INSTALL
# ══════════════════════════════════════════════════════════════════════════════
def pip(*pkgs):
    print(f"📦 {pkgs[0].split('>=')[0].split('==')[0]}...")
    subprocess.check_call([sys.executable,"-m","pip","install","-q",*pkgs])

pip("fastapi>=0.110.0","uvicorn[standard]>=0.29.0",
    "pydantic>=2.6.0,<3.0.0","pydantic-settings>=2.2.0",
    "python-dotenv","aiofiles","httpx","python-multipart")

pip("langchain>=0.2.0","langchain-groq>=0.1.6","langchain-core>=0.2.0",
    "langchain-community>=0.2.0","langchain-huggingface>=0.0.6","groq>=0.9.0")

pip("faiss-cpu","sentence-transformers>=2.7.0")
pip("presidio-analyzer","presidio-anonymizer")
pip("scikit-learn","xgboost","pandas","numpy","kagglehub")
pip("pyngrok>=7.0.0","nest-asyncio","twilio")

if APP_MODE == 2:
    pip("supabase","redis","langdetect")
    if REDIS_URL:
        pip("redis")
    print("📦 Mode 2: LaBSE multilingual embeddings (downloading ~1GB)...")
    pip("sentence-transformers>=2.7.0")  # LaBSE is included

if INSTALL_WHISPER:
    pip("openai-whisper")
    subprocess.call(["apt-get","install","-qq","ffmpeg"])

if INSTALL_MEDIAPIPE:
    pip("mediapipe","opencv-python-headless")

if INSTALL_LIBROSA:
    pip("librosa","soundfile")

print("🔤 spaCy model...")
subprocess.check_call([sys.executable,"-m","spacy","download","en_core_web_lg","-q"])
print("✅ All dependencies installed\n")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 3: ENVIRONMENT
# ══════════════════════════════════════════════════════════════════════════════
os.environ["GROQ_API_KEY"]           = GROQ_API_KEY
os.environ["NGROK_AUTH_TOKEN"]       = NGROK_AUTH_TOKEN
os.environ["APP_MODE"]               = str(APP_MODE)
os.environ["TWILIO_ACCOUNT_SID"]     = TWILIO_ACCOUNT_SID
os.environ["TWILIO_AUTH_TOKEN"]      = TWILIO_AUTH_TOKEN_VAL
os.environ["TWILIO_WHATSAPP_FROM"]   = TWILIO_WHATSAPP_FROM

if APP_MODE == 2:
    if SUPABASE_URL:  os.environ["SUPABASE_URL"] = SUPABASE_URL
    if SUPABASE_KEY:  os.environ["SUPABASE_KEY"] = SUPABASE_KEY
    if REDIS_URL:     os.environ["REDIS_URL"]     = REDIS_URL
    if FITBIT_CLIENT_ID:
        os.environ["FITBIT_CLIENT_ID"]     = FITBIT_CLIENT_ID
        os.environ["FITBIT_CLIENT_SECRET"] = FITBIT_CLIENT_SECRET
    if GOOGLE_FIT_CLIENT_ID:
        os.environ["GOOGLE_FIT_CLIENT_ID"]     = GOOGLE_FIT_CLIENT_ID
        os.environ["GOOGLE_FIT_CLIENT_SECRET"] = GOOGLE_FIT_SECRET

if KAGGLE_USERNAME:
    os.environ["KAGGLE_USERNAME"] = KAGGLE_USERNAME
    os.environ["KAGGLE_KEY"]      = KAGGLE_KEY

if TWILIO_ACCOUNT_SID:
    os.environ["ENABLE_WHATSAPP"] = "true"

mode_label = "🧪 TESTING (Mode 1)" if APP_MODE == 1 else "🏢 BUSINESS (Mode 2)"
print(f"✅ Environment set — {mode_label}")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 4: SUPABASE SETUP REMINDER (Mode 2 only)
# ══════════════════════════════════════════════════════════════════════════════
if APP_MODE == 2 and SUPABASE_URL:
    from data.db import get_supabase_setup_sql
    print("\n📋 Run this SQL in your Supabase project once:")
    print("   supabase.com → SQL Editor → paste → run")
    print("-"*50)
    print(get_supabase_setup_sql())
    print("-"*50)

# ══════════════════════════════════════════════════════════════════════════════
# STEP 5: TRAIN ML
# ══════════════════════════════════════════════════════════════════════════════
if TRAIN_ML:
    print("\n🧠 Training ML Triage (RF + XGBoost)...")
    try:
        from services.ml_triage import train_triage_models
        m = train_triage_models(use_kaggle=USE_KAGGLE_DATA, force_retrain=False)
        s = m.get("status","?")
        if s == "trained":
            print(f"✅ Trained on '{m.get('data_source','?')}' | Acc: {m.get('accuracy','?')} | CV: {m.get('cv_mean','?')}")
        elif s == "loaded_from_cache":
            print("✅ Cached model loaded")
        else:
            print(f"⚠️  {s} — rule-based fallback active")
    except Exception as e:
        print(f"⚠️  ML skipped: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 6: NGROK + SERVER
# ══════════════════════════════════════════════════════════════════════════════
from pyngrok import ngrok
import threading, uvicorn

ngrok.kill()
ngrok.set_auth_token(NGROK_AUTH_TOKEN)
tunnel     = ngrok.connect(8000)
public_url = tunnel.public_url

# Update APP_BASE_URL for OAuth callbacks
os.environ["APP_BASE_URL"] = public_url

print("\n" + "="*65)
print(f"  🚀  SentinelMind v5 LIVE — {mode_label}")
print("="*65)
print(f"  URL         : {public_url}")
print(f"  Docs        : {public_url}/docs")
print(f"  Health      : {public_url}/health")
print(f"  Mode        : {APP_MODE} ({'Testing' if APP_MODE==1 else 'Business'})")
print(f"  Chat        : POST {public_url}/api/chat")
print(f"  Silent mood : POST {public_url}/api/silent/emoji")
print(f"  Consent     : GET  {public_url}/api/consent/dashboard/{{user_id}}")
print(f"  Baseline    : GET  {public_url}/api/baseline/status/{{user_id}}")
print(f"  Wearable    : GET  {public_url}/api/wearable/fitbit/connect/{{user_id}}")
print(f"  Jobs        : GET  {public_url}/api/jobs/roles")
print(f"  WhatsApp WH : {public_url}/api/whatsapp/incoming")
print("="*65)
print("  Paste Public URL into your frontend .env as REACT_APP_API_URL")
print("="*65 + "\n")

from main import app

def run():
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")

threading.Thread(target=run, daemon=True).start()
print("✅ Server running in background. Other cells are free to use.")
print(f"   Quick test: import requests; print(requests.get('{public_url}/health').json())")
