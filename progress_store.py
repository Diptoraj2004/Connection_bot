import os, json
from datetime import datetime
from config import BACKUP_DIR, LOCAL_SAVE_PATH, USER_ID

os.makedirs(BACKUP_DIR,exist_ok=True)

def save_user_state(state):
    path = os.path.join(BACKUP_DIR,"state.json")
    if os.path.exists(LOCAL_SAVE_PATH):
        with open(LOCAL_SAVE_PATH) as f: data = json.load(f)
    else: data = {}
    data[USER_ID] = state
    with open(LOCAL_SAVE_PATH,"w") as f:
        json.dump(data,f,indent=2)

def load_user_state():
    if os.path.exists(LOCAL_SAVE_PATH):
        data = json.load(open(LOCAL_SAVE_PATH))
        return data.get(USER_ID,{})
    return {}

def record_mood(mood:str):
    state = load_user_state()
    state.setdefault("mood_log",[]).append({"ts":datetime.now().isoformat(),"mood":mood})
    save_user_state(state)

def record_sleep(hours:int):
    state = load_user_state()
    state.setdefault("sleep_log",[]).append({"ts":datetime.now().isoformat(),"hours":hours})
    save_user_state(state)

def get_current_streak():
    state = load_user_state()
    log = state.get("mood_log",[])
    if not log: return 0
    today = datetime.now().date()
    streak = 0
    for entry in reversed(log):
        d = datetime.fromisoformat(entry["ts"]).date()
        if (today-d).days==streak: streak+=1
        else: break
    return streak

def record_escalation(reason:str):
    state = load_user_state()
    state.setdefault("escalation_log",[]).append({"ts":datetime.now().isoformat(),"reason":reason})
    save_user_state(state)
