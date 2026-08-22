// sentinel_api.js — SentinelMind v5 Bridge
// Drop this file into your dashboard/src/ folder.
// Change ONE line when backend URL changes. Everything else stays the same.
// Works with v5 and all future versions.

const BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";
const call = async (method, path, body) => {
  const r = await fetch(`${BASE}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!r.ok) throw new Error(`${method} ${path} → ${r.status}`);
  return r.json();
};

export const API = {
  // CHAT
  chat: (user_id, message, reset = false) =>
    call("POST", "/api/chat", { user_id, message, reset_session: reset }),
  chatHistory: (user_id) => call("GET", `/api/chat/history/${user_id}`),
  resetSession: (user_id) => call("DELETE", `/api/chat/session/${user_id}`),

  // SILENT (no words needed)
  emoji: (user_id, emoji) => call("POST", "/api/silent/emoji", { user_id, emoji }),
  weather: (user_id, weather) => call("POST", "/api/silent/weather", { user_id, weather }),
  dailyChallenge: (user_id) => call("GET", `/api/silent/challenge/${user_id}`),
  completeChallenge: (user_id, challenge_id, felt_better = null) =>
    call("POST", "/api/silent/challenge/complete", { user_id, challenge_id, felt_better }),
  appOpen: (user_id) => call("POST", `/api/silent/open/${user_id}`),
  silentOptions: () => call("GET", "/api/silent/options"),

  // CONSENT
  consentDashboard: (user_id) => call("GET", `/api/consent/dashboard/${user_id}`),
  grantConsent: (user_id, feature) =>
    call("POST", `/api/consent/grant/${user_id}/${feature}`),
  revokeConsent: (user_id, feature) =>
    call("POST", `/api/consent/revoke/${user_id}/${feature}`),
  revokeAll: (user_id) => call("POST", `/api/consent/revoke-all/${user_id}`),
  consentStatus: (user_id) => call("GET", `/api/consent/status/${user_id}`),

  // SCREENING
  questionnaires: () => call("GET", "/api/screening/questionnaires"),
  questionnaire: (test_name) => call("GET", `/api/screening/questionnaire/${test_name}`),
  score: (user_id, test_name, answers) =>
    call("POST", "/api/screening/score", { user_id, test_name, answers }),
  screeningResults: (user_id) => call("GET", `/api/screening/results/${user_id}`),
  inferTest: (text) => call("GET", `/api/screening/infer?text=${encodeURIComponent(text)}`),

  // PROGRESS & MOOD
  progress: (user_id) => call("GET", `/api/progress/${user_id}`),
  logMood: (user_id, mood_score, mood_label, note = "") =>
    call("POST", "/api/progress/mood", { user_id, mood_score, mood_label, note }),
  moodHistory: (user_id) => call("GET", `/api/progress/mood-history/${user_id}`),

  // ENGAGEMENT (non-clinical hooks)
  logStudy: (user_id, duration_minutes, subject = "", focus_self_rating = 5) =>
    call("POST", "/api/engage/study", { user_id, duration_minutes, subject, focus_self_rating }),
  studyStats: (user_id) => call("GET", `/api/engage/study/${user_id}`),
  logSleep: (user_id, sleep_hours, sleep_quality, bedtime_hour = 23, wake_hour = 7) =>
    call("POST", "/api/engage/sleep", { user_id, sleep_hours, sleep_quality, bedtime_hour, wake_hour }),
  sleepLeaderboard: (college_id = "default") =>
    call("GET", `/api/engage/sleep/leaderboard?college_id=${college_id}`),
  logMusic: (user_id, track_name, artist, genre_tags = [], self_mood = "") =>
    call("POST", "/api/engage/music", { user_id, track_name, artist, genre_tags, self_mood }),
  musicTrend: (user_id) => call("GET", `/api/engage/music/trend/${user_id}`),
  addExam: (user_id, subject, exam_date) =>
    call("POST", "/api/engage/exam", { user_id, subject, exam_date }),
  upcomingExams: (user_id) => call("GET", `/api/engage/exams/${user_id}`),
  sendPeerPing: (from_user_id, to_user_id, message_type = "check_in") =>
    call("POST", "/api/engage/peer-ping", { from_user_id, to_user_id, message_type }),
  myPings: (user_id) => call("GET", `/api/engage/peer-pings/${user_id}`),

  // LOGBOOK
  saveLogbook: (user_id, content, consent_level = "counselor_only") =>
    call("POST", "/api/logbook/entry", { user_id, content, consent_level, share_uplifting: true }),
  getLogbook: (user_id, requester_role = "student") =>
    call("GET", `/api/logbook/${user_id}?requester_role=${requester_role}`),

  // RESOURCES
  resources: (mood = "neutral") => call("GET", `/api/resources?mood=${mood}`),
  music: (mood = "neutral") => call("GET", `/api/resources/music?mood=${mood}`),

  // STORIES
  stories: (condition = "") =>
    call("GET", `/api/stories${condition ? `?condition=${condition}` : ""}`),
  matchStories: (user_id, condition = "") =>
    call("GET", `/api/stories/match/${user_id}${condition ? `?condition=${condition}` : ""}`),
  submitStory: (user_id, title, content, condition, what_helped = []) =>
    call("POST", "/api/stories/submit", { user_id, title, content, condition, what_helped }),

  // BOOKING
  slots: (mode = "") => call("GET", `/api/booking/slots${mode ? `?mode=${mode}` : ""}`),
  book: (user_id, counselor_id = "campus_default", anonymous = true) =>
    call("POST", "/api/booking/slot", { user_id, counselor_id, anonymous }),
  myBookings: (user_id) => call("GET", `/api/booking/my-bookings/${user_id}`),

  // IOT
  iotReading: (user_id, metric_type, value) =>
    call("POST", "/api/iot/reading", { user_id, metric_type, value }),
  simulateIot: (user_id, profile = "stressed") =>
    call("POST", `/api/iot/simulate/${user_id}?profile=${profile}`),
  iotSummary: (user_id) => call("GET", `/api/iot/summary/${user_id}`),

  // WEARABLE
  fitbitConnect: (user_id) => call("GET", `/api/wearable/fitbit/connect/${user_id}`),
  fitbitSync: (user_id) => call("POST", `/api/wearable/fitbit/sync/${user_id}`),
  googleFitConnect: (user_id) => call("GET", `/api/wearable/google-fit/connect/${user_id}`),
  connectedDevices: (user_id) => call("GET", `/api/wearable/devices/${user_id}`),
  disconnectDevice: (user_id, device) =>
    call("DELETE", `/api/wearable/devices/${user_id}/${device}`),

  // BASELINE
  baselineStatus: (user_id) => call("GET", `/api/baseline/status/${user_id}`),
  baselineAll: (user_id) => call("GET", `/api/baseline/all/${user_id}`),

  // PASSIVE
  analyzeCamera: (user_id, frame_b64) =>
    call("POST", "/api/passive/camera/analyze", { user_id, frame_b64 }),
  recordTyping: (user_id, message_length, typing_duration_s, backspace_count, total_keystrokes) =>
    call("POST", "/api/passive/typing/record",
      { user_id, message_length, typing_duration_s, backspace_count, total_keystrokes }),
  usagePattern: (user_id) => call("GET", `/api/passive/usage/${user_id}`),
  iotDevices: () => call("GET", "/api/passive/iot/devices"),

  // ESCALATION (counselor dashboard)
  activeEscalations: () => call("GET", "/api/escalation/active"),
  userEscalation: (user_id) => call("GET", `/api/escalation/active/${user_id}`),
  acknowledgeEscalation: (event_id, acknowledged_by, note = "") =>
    call("POST", "/api/escalation/acknowledge", { event_id, acknowledged_by, note }),
  resolveEscalation: (event_id, resolved_by, outcome) =>
    call("POST", "/api/escalation/resolve", { event_id, resolved_by, outcome }),

  // ADMIN
  trends: () => call("GET", "/api/admin/trends"),
  alerts: () => call("GET", "/api/admin/alerts"),
  verifyLedger: () => call("GET", "/api/admin/ledger/verify"),

  // COUNSELOR
  counselorCapacity: () => call("GET", "/api/counselor/capacity"),
  counselorNotes: (counselor_id, payload) =>
    call("POST", "/api/counselor/notes", { counselor_id, ...payload }),
  counselorStats: () => call("GET", "/api/counselor/stats"),

  // VOLUNTEERS
  registerVolunteer: (payload) => call("POST", "/api/volunteer/register", payload),
  volunteerLoad: () => call("GET", "/api/volunteer/load"),

  // NGO
  searchNgos: (condition = "", max_cost_inr = 0) =>
    call("GET", `/api/ngo/search?condition=${condition}&max_cost_inr=${max_cost_inr}`),

  // RATING
  submitRating: (user_id, target_type, target_id, score, comment = "") =>
    call("POST", "/api/rating", { user_id, target_type, target_id, score, comment }),
  getRatings: (target_type, target_id) =>
    call("GET", `/api/rating/${target_type}/${target_id}`),

  // VOICE
  voiceStatus: () => call("GET", "/api/voice/status"),
  transcribe: (user_id, audio_b64, extension = "webm") =>
    call("POST", "/api/voice/transcribe", { user_id, audio_b64, extension }),

  // WHATSAPP
  waStatus: () => call("GET", "/api/whatsapp/status"),

  // JOBS
  jobRoles: () => call("GET", "/api/jobs/roles"),
  applyJob: (payload) => call("POST", "/api/jobs/apply", payload),
  jobsImpact: () => call("GET", "/api/jobs/impact"),

  // ML
  mlStatus: () => call("GET", "/api/ml/status"),
  trainModel: (use_kaggle = true) =>
    call("POST", "/api/ml/train", { use_kaggle, force_retrain: false }),

  // SYSTEM
  health: () => call("GET", "/health"),
};

export default API;

// ── NEW IN V5.1 ──────────────────────────────────────────────────────────────

// PHENOTYPING (no hardware, software-only signals)
API.recordTyping = (user_id, message, typing_duration_s=0, backspace_count=0, total_keystrokes=0) =>
  call("POST", "/api/phenotype/typing", {user_id, message, typing_duration_s, backspace_count, total_keystrokes});
API.crossSessionRisk = (user_id) => call("GET", `/api/phenotype/cross-session/${user_id}`);

// CONVERSATION MEMORY
API.memory = (user_id) => call("GET", `/api/memory/${user_id}`);
API.recordTechnique = (user_id, technique, helped=null) =>
  call("POST", "/api/memory/technique", {user_id, technique, helped});
API.toneRules = (user_id, state) => call("GET", `/api/memory/tone/${user_id}/${state}`);

// ZONES (story-based unlocks, not point scores)
API.zones = (user_id) => call("GET", `/api/zones/${user_id}`);
API.allZones = () => call("GET", "/api/zones/all");

// PAYMENT
API.pricing = () => call("GET", "/api/payment/pricing");
API.createInvoice = (institution_id, institution_name, student_count, contact_email, tier="standard") =>
  call("POST", "/api/payment/invoice", {institution_id, institution_name, student_count, contact_email, tier});
