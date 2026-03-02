"""
ARTIFICIAL & INTELLIGENT
AI Business Command Dashboard
LM Studio (Llama-3.2-1B-Instruct-Q5_K_M) + Ollama + OpenAI triple-fallback
"""
import streamlit as st
import json, os, re, time, socket
from datetime import datetime
from pathlib import Path

try:
    import openai; OPENAI_LIB = True
except ImportError:
    OPENAI_LIB = False

try:
    import requests
    from bs4 import BeautifulSoup
    WEB_LIB = True
except ImportError:
    WEB_LIB = False

try:
    import plotly.graph_objects as go
    import pandas as pd
    CHART_LIB = True
except ImportError:
    CHART_LIB = False

# ── Paths ─────────────────────────────────────────────────────────────────────
DATA = Path("data"); DATA.mkdir(exist_ok=True)
SF   = DATA/"settings.json"
PF   = DATA/"products.json"
RF   = DATA/"revenue.json"
TF   = DATA/"tasks.json"
AVF  = DATA/"avatars.json"
LF   = DATA/"leads.json"
CF   = DATA/"chat.json"
TASKF= DATA/"tasksheet.json"
WINSF= DATA/"wins.json"
CLIF = DATA/"clients.json"

# ── Helpers ───────────────────────────────────────────────────────────────────
def jload(p, d):
    try: return json.loads(p.read_text()) if p.exists() else d
    except: return d

def jsave(p, d):
    p.write_text(json.dumps(d, indent=2))

def check_online():
    try:
        socket.setdefaulttimeout(2)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
        return True
    except: return False

def get_weather(city, api_key):
    if not api_key or not city: return None
    try:
        r = requests.get(
            f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric",
            timeout=4)
        d = r.json()
        if r.status_code == 200:
            return {"temp": round(d["main"]["temp"]), "desc": d["weather"][0]["description"].title(),
                    "city": d["name"], "icon": d["weather"][0]["main"]}
    except: pass
    return None

def scrape_emails(text):
    return list(set(re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)))

def send_telegram(msg):
    s = jload(SF, {})
    token = s.get("telegram_token", "")
    chat_id = s.get("telegram_chat_id", "")
    if not token or not chat_id: return False
    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"}, timeout=5)
        return True
    except: return False

# ── AI Engine — LM Studio → Ollama → OpenAI ──────────────────────────────────
def ai_call(prompt, system="You are a helpful AI business assistant.", max_tokens=1200):
    s = jload(SF, {})

    # 1. LM Studio (your Llama-3.2-1B-Instruct-Q5_K_M via Hugging Face)
    lm_url   = s.get("lm_studio_url", "http://localhost:1234/v1")
    lm_model = s.get("lm_model", "Llama-3.2-1B-Instruct-Q5_K_M")
    if lm_url and OPENAI_LIB:
        try:
            client = openai.OpenAI(api_key="lm-studio", base_url=lm_url)
            resp = client.chat.completions.create(
                model=lm_model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                max_tokens=max_tokens, temperature=0.7, timeout=30)
            return resp.choices[0].message.content.strip(), "LM Studio (Llama-3.2)"
        except: pass

    # 2. Ollama
    ol_url   = s.get("ollama_url", "http://localhost:11434/v1")
    ol_model = s.get("ollama_model", "llama3.2:1b")
    if OPENAI_LIB:
        try:
            client = openai.OpenAI(api_key="ollama", base_url=ol_url)
            resp = client.chat.completions.create(
                model=ol_model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                max_tokens=max_tokens, timeout=30)
            return resp.choices[0].message.content.strip(), "Ollama (Llama)"
        except: pass

    # 3. OpenAI
    oai_key = s.get("openai_key", "")
    if oai_key and OPENAI_LIB:
        try:
            client = openai.OpenAI(api_key=oai_key)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                max_tokens=max_tokens)
            return resp.choices[0].message.content.strip(), "OpenAI GPT-4o-mini"
        except Exception as e:
            return f"[AI Error: {e}]", "Error"

    return None, "Offline — No AI Engine"

# ── Default data ──────────────────────────────────────────────────────────────
DEFAULT_SETTINGS = {
    "openai_key": "", "lm_studio_url": "http://localhost:1234/v1",
    "lm_model": "Llama-3.2-1B-Instruct-Q5_K_M",
    "ollama_url": "http://localhost:11434/v1", "ollama_model": "llama3.2:1b",
    "telegram_token": "", "telegram_chat_id": "",
    "weather_city": "Sydney", "weather_key": ""
}

DEFAULT_PRODUCTS = [
    {"name":"Email Assassin","price":97,"billing":"month","status":"Live","customers":12,"mrr":1164,
     "checklist":{"Code written":True,"Test with real emails":False,"Connect OpenAI API":False,"Deploy to production":False,"Landing page":False,"Launch":False}},
    {"name":"Lead Generator & Scraper","price":697,"billing":"month","status":"Live","customers":3,"mrr":2091,
     "checklist":{"Code written":True,"Test scraping":False,"LinkedIn integration":False,"Email verification":False,"Export CSV":False,"Deploy":False}},
    {"name":"Podcast Generator","price":297,"billing":"month","status":"Beta","customers":1,"mrr":297,
     "checklist":{"Code written":True,"Test audio generation":False,"Connect ElevenLabs":False,"Full workflow test":False,"Deploy":False}},
    {"name":"Website Redesigner (SiteGlow AI)","price":497,"billing":"once","status":"Ready","customers":0,"mrr":0,
     "checklist":{"Code written":True,"Test with real websites":False,"Improve HTML/CSS gen":False,"Add download ZIP":False,"Deploy":False}},
    {"name":"Launch Kit AI","price":297,"billing":"month","status":"Ready","customers":0,"mrr":0,
     "checklist":{"Concept mapped":True,"Build 8 modules":False,"Test business plan gen":False,"Test contract templates":False,"Deploy":False}},
    {"name":"LinkedIn Post Generator","price":97,"billing":"month","status":"Ready","customers":0,"mrr":0,
     "checklist":{"Code written":True,"Test post quality":False,"Add templates library":False,"Deploy":False}},
    {"name":"Proposal Machine","price":497,"billing":"month","status":"Ready","customers":0,"mrr":0,
     "checklist":{"Code written":True,"Test proposal gen":False,"Add PDF export":False,"Deploy":False}},
    {"name":"Meeting Genius","price":197,"billing":"month","status":"Ready","customers":0,"mrr":0,
     "checklist":{"Code written":True,"Test with meeting notes":False,"Calendar integration":False,"Deploy":False}},
    {"name":"Content Factory","price":397,"billing":"month","status":"Ready","customers":0,"mrr":0,
     "checklist":{"Code written":True,"Test 30-day calendar":False,"Multi-platform support":False,"Deploy":False}},
    {"name":"Sales Script Generator","price":297,"billing":"month","status":"Ready","customers":0,"mrr":0,
     "checklist":{"Code written":True,"Test script quality":False,"Add objection handlers":False,"Deploy":False}},
    {"name":"Pitch Deck Creator","price":497,"billing":"once","status":"Ready","customers":0,"mrr":0,
     "checklist":{"Code written":True,"Test deck generation":False,"Add PowerPoint export":False,"Deploy":False}},
    {"name":"Competitor Spy","price":497,"billing":"month","status":"Ready","customers":0,"mrr":0,
     "checklist":{"Code written":True,"Test website scraping":False,"Add competitive analysis":False,"Deploy":False}},
    {"name":"TradieTech Suite","price":197,"billing":"month","status":"Ready","customers":0,"mrr":0,
     "checklist":{"Quote Generator":False,"Invoice Creator":False,"Job Scheduler":False,"Client Follow-up":False,"Marketing posts":False,"Bundle & test":False,"Deploy":False}},
    {"name":"Magic Mike Builder","price":2997,"billing":"once","status":"Ready","customers":0,"mrr":0,
     "checklist":{"Avatar creation (HeyGen)":False,"Voice generation (ElevenLabs)":False,"Script writing (GPT-4)":False,"Video creation automation":False,"Platform publishing":False,"Comment response automation":False,"Revenue tracking":False}},
    {"name":"AI Sales Rep","price":1497,"billing":"month","status":"Concept","customers":0,"mrr":0,
     "checklist":{"24/7 lead qualification":False,"Demo booking automation":False,"Follow-up sequences":False,"Deploy":False}},
]

for f, d in [(SF, DEFAULT_SETTINGS), (PF, DEFAULT_PRODUCTS), (RF, {"today": 0, "history": []}),
             (TF, []), (AVF, []), (LF, []), (CF, []), (TASKF, []), (WINSF, []), (CLIF, [])]:
    if not f.exists(): jsave(f, d)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="ARTIFICIAL & INTELLIGENT", page_icon="⚡", layout="wide",
                   initial_sidebar_state="expanded")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&display=swap');
*{font-family:'Inter',sans-serif!important;}

/* ── Core background ── */
.stApp{background:#000!important;color:#f0f0f0;}
section[data-testid="stSidebar"]{background:rgba(5,5,5,0.95)!important;border-right:1px solid #1a1a1a;}

/* ── Typography ── */
h1{color:#ff0080!important;text-shadow:0 0 30px rgba(255,0,128,.4),0 0 60px rgba(255,0,128,.15);font-weight:900;letter-spacing:-1px;}
h2{color:#fff!important;font-weight:700;}
h3{color:#00ff41!important;font-weight:600;text-shadow:0 0 12px rgba(0,255,65,.25);}

/* ── Buttons ── */
.stButton>button{
  background:linear-gradient(135deg,#ff0080 0%,#c0006a 50%,#00ff41 100%)!important;
  color:#fff!important;font-weight:700!important;border:none!important;
  border-radius:8px!important;transition:all .25s!important;
  box-shadow:0 2px 12px rgba(255,0,128,.2)!important;}
.stButton>button:hover{
  box-shadow:0 0 25px rgba(255,0,128,.5),0 0 50px rgba(0,255,65,.2)!important;
  transform:translateY(-1px) scale(1.02)!important;}

/* ── Inputs ── */
.stTextInput>div>div>input,.stTextArea>div>div>textarea{
  background:rgba(10,10,10,0.85)!important;
  border:1px solid rgba(255,0,128,.25)!important;
  color:#f0f0f0!important;border-radius:8px!important;
  backdrop-filter:blur(10px)!important;}
.stTextInput>div>div>input:focus,.stTextArea>div>div>textarea:focus{
  border-color:#ff0080!important;box-shadow:0 0 12px rgba(255,0,128,.3)!important;}
.stSelectbox>div>div{
  background:rgba(10,10,10,0.85)!important;
  border:1px solid rgba(255,0,128,.2)!important;color:#f0f0f0!important;
  border-radius:8px!important;}

/* ── Glass cards ── */
.card{
  background:rgba(12,12,12,0.75);
  border:1px solid rgba(255,255,255,0.06);
  border-radius:14px;padding:16px 18px;margin-bottom:12px;
  backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);
  box-shadow:0 4px 24px rgba(0,0,0,.4);}
.card-g{border-left:3px solid #00ff41;box-shadow:0 4px 24px rgba(0,0,0,.4),-2px 0 12px rgba(0,255,65,.1);}
.card-p{border-left:3px solid #ff0080;box-shadow:0 4px 24px rgba(0,0,0,.4),-2px 0 12px rgba(255,0,128,.1);}
.card-b{border-left:3px solid #00bfff;box-shadow:0 4px 24px rgba(0,0,0,.4),-2px 0 12px rgba(0,191,255,.1);}
.card-y{border-left:3px solid #ffd700;box-shadow:0 4px 24px rgba(0,0,0,.4),-2px 0 12px rgba(255,215,0,.1);}

/* ── Metrics ── */
[data-testid="stMetricValue"]{color:#00ff41!important;font-weight:800!important;text-shadow:0 0 10px rgba(0,255,65,.3);}
[data-testid="stMetricLabel"]{color:#555!important;font-size:.78em!important;}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"]{
  background:rgba(6,6,6,0.9);border-bottom:1px solid rgba(255,0,128,.15);
  backdrop-filter:blur(10px);}
.stTabs [data-baseweb="tab"]{color:#444!important;font-size:.82em!important;font-weight:600!important;}
.stTabs [aria-selected="true"]{
  color:#ff0080!important;
  border-bottom:2px solid #ff0080!important;
  text-shadow:0 0 10px rgba(255,0,128,.4)!important;}

/* ── Chat bubbles ── */
.chat-user{
  background:rgba(0,255,65,.05);border-left:3px solid #00ff41;
  padding:12px 16px;border-radius:10px;margin:6px 0;
  backdrop-filter:blur(10px);}
.chat-ai{
  background:rgba(255,0,128,.05);border-left:3px solid #ff0080;
  padding:12px 16px;border-radius:10px;margin:6px 0;
  backdrop-filter:blur(10px);}
.chat-sys{
  background:rgba(0,191,255,.04);border-left:3px solid #00bfff;
  padding:10px 16px;border-radius:8px;margin:4px 0;font-size:.82em;}

/* ── Status pills ── */
.pill-on{background:rgba(0,42,10,.8);color:#00ff41;padding:4px 12px;border-radius:20px;
  font-size:.75em;font-weight:700;display:inline-block;border:1px solid rgba(0,255,65,.2);}
.pill-off{background:rgba(42,0,0,.8);color:#ff4444;padding:4px 12px;border-radius:20px;
  font-size:.75em;font-weight:700;display:inline-block;border:1px solid rgba(255,68,68,.2);}
.pill-ai{background:rgba(10,10,42,.8);color:#00bfff;padding:4px 12px;border-radius:20px;
  font-size:.75em;font-weight:700;display:inline-block;border:1px solid rgba(0,191,255,.2);}

/* ── Clock & weather boxes ── */
.clock-box{
  background:rgba(5,5,5,0.8);border:1px solid rgba(255,0,128,.3);
  border-radius:12px;padding:10px 20px;text-align:center;
  backdrop-filter:blur(20px);box-shadow:0 0 20px rgba(255,0,128,.1);}
.weather-box{
  background:rgba(5,5,5,0.8);border:1px solid rgba(0,191,255,.2);
  border-radius:12px;padding:10px 16px;text-align:center;
  backdrop-filter:blur(20px);}

/* ── Login screen ── */
.login-wrap{
  max-width:400px;margin:80px auto;padding:40px;
  background:rgba(8,8,8,0.9);border:1px solid rgba(255,0,128,.3);
  border-radius:20px;backdrop-filter:blur(30px);
  box-shadow:0 0 60px rgba(255,0,128,.15),0 0 120px rgba(0,255,65,.05);}

/* ── Scrollbar ── */
::-webkit-scrollbar{width:4px;}
::-webkit-scrollbar-track{background:#000;}
::-webkit-scrollbar-thumb{background:rgba(255,0,128,.3);border-radius:2px;}

/* ── Progress bars ── */
.stProgress>div>div{background:linear-gradient(90deg,#ff0080,#00ff41)!important;}

/* ── Dividers ── */
hr{border-color:rgba(255,255,255,.04)!important;}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
for k, v in [("online", False), ("online_ts", 0), ("weather", None), ("weather_ts", 0), ("authenticated", False)]:
    if k not in st.session_state: st.session_state[k] = v

# ── LOGIN GATE ────────────────────────────────────────────────────────────────
DASH_PASSWORD = "258088"

if not st.session_state.authenticated:
    st.markdown("""
    <div style='max-width:420px;margin:80px auto;padding:44px 40px;
      background:rgba(8,8,8,0.92);border:1px solid rgba(255,0,128,.35);
      border-radius:20px;backdrop-filter:blur(30px);
      box-shadow:0 0 60px rgba(255,0,128,.15),0 0 120px rgba(0,255,65,.05);'>
      <h1 style='text-align:center;margin:0 0 4px 0;font-size:1.7em;letter-spacing:-1px;'>⚡ ARTIFICIAL</h1>
      <h1 style='text-align:center;margin:0 0 20px 0;font-size:1.7em;letter-spacing:-1px;color:#00ff41!important;'>&amp; INTELLIGENT</h1>
      <p style='text-align:center;color:#444;font-size:.82em;letter-spacing:2px;margin-bottom:28px;'>COMMAND DASHBOARD · ARMOURVAULT.AU</p>
    </div>
    """, unsafe_allow_html=True)
    col_l, col_m, col_r = st.columns([1, 1.2, 1])
    with col_m:
        pw = st.text_input("Password", type="password", placeholder="Enter access code", label_visibility="collapsed")
        if st.button("⚡ ACCESS DASHBOARD", use_container_width=True, type="primary"):
            if pw == DASH_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password.")
        st.markdown("<p style='text-align:center;color:#222;font-size:.72em;margin-top:16px;'>ArmourVault.au &nbsp;·&nbsp; Authorised Access Only</p>", unsafe_allow_html=True)
    st.stop()

# ── Load all data ─────────────────────────────────────────────────────────────
S        = jload(SF, DEFAULT_SETTINGS)
products = jload(PF, DEFAULT_PRODUCTS)
revenue  = jload(RF, {"today": 0, "history": []})
tasks    = jload(TF, [])
avatars  = jload(AVF, [])
leads    = jload(LF, [])
chat_hist= jload(CF, [])
tasksheet= jload(TASKF, [])
wins     = jload(WINSF, [])
clients  = jload(CLIF, [])

# ── Online check (cached 60s) ─────────────────────────────────────────────────
if time.time() - st.session_state.online_ts > 60:
    st.session_state.online = check_online()
    st.session_state.online_ts = time.time()
online = st.session_state.online

# ── Weather (cached 10min) ────────────────────────────────────────────────────
if (time.time() - st.session_state.weather_ts > 600 and online
        and S.get("weather_key") and S.get("weather_city")):
    st.session_state.weather = get_weather(S["weather_city"], S["weather_key"])
    st.session_state.weather_ts = time.time()
weather = st.session_state.weather

# ── Computed totals ───────────────────────────────────────────────────────────
now = datetime.now()
total_mrr = sum(p.get("mrr", 0) for p in products)
total_customers = sum(p.get("customers", 0) for p in products)
pending_tasks = [t for t in tasksheet if not t.get("done")]
done_today = [t for t in tasksheet if t.get("done") and t.get("date", "") == now.strftime("%Y-%m-%d")]

# ── HEADER ────────────────────────────────────────────────────────────────────
weather_html = ""
if weather:
    icons = {"Clear":"☀️","Clouds":"☁️","Rain":"🌧️","Thunderstorm":"⛈️","Snow":"❄️","Mist":"🌫️","Drizzle":"🌦️","Haze":"🌫️"}
    wi = icons.get(weather["icon"], "🌡️")
    weather_html = f"""<div class='weather-box'>{wi} <strong style='color:#00bfff;font-size:1.1em;'>{weather['temp']}°C</strong><br>
    <span style='color:#555;font-size:.75em;'>{weather['desc']} · {weather['city']}</span></div>"""

pill = '<span class="pill-on">🟢 ONLINE</span>' if online else '<span class="pill-off">🔴 OFFLINE</span>'

clock_html = f"""
<div style='background:rgba(5,5,5,0.85);border:1px solid rgba(255,0,128,.35);
  border-radius:12px;padding:10px 20px;text-align:center;
  backdrop-filter:blur(20px);box-shadow:0 0 20px rgba(255,0,128,.1);'>
  <div style='color:#00ff41;font-size:1.8em;font-weight:900;letter-spacing:3px;'>{now.strftime('%H:%M')}</div>
  <div style='color:#555;font-size:.72em;'>{now.strftime('%A %d %B %Y')}</div>
</div>"""

st.markdown(f"""
<div style='display:flex;justify-content:space-between;align-items:center;padding:0 0 8px 0;flex-wrap:wrap;gap:10px;'>
  <div>
    <h1 style='margin:0;font-size:2em;letter-spacing:-2px;color:#ff0080;
      text-shadow:0 0 30px rgba(255,0,128,.4);'>
      ⚡ ARTIFICIAL <span style="color:#00ff41;text-shadow:0 0 20px rgba(0,255,65,.4);">&amp;</span> INTELLIGENT
    </h1>
    <p style='color:#444;margin:3px 0 0 0;font-size:.78em;letter-spacing:3px;text-transform:uppercase;'>
      AI Business Command Dashboard &nbsp;·&nbsp; ArmourVault.au
    </p>
  </div>
  <div style='display:flex;gap:12px;align-items:center;flex-wrap:wrap;'>
    {weather_html}
    {clock_html}
    <div style='text-align:center;'>{pill}<br>
      <span style='color:#333;font-size:.68em;'>Llama-3.2-1B · LM Studio</span>
    </div>
  </div>
</div>
<hr style='border:none;border-top:1px solid rgba(255,255,255,.04);margin:0 0 12px 0;'>
""", unsafe_allow_html=True)

# ── KPI Row ───────────────────────────────────────────────────────────────────
k1,k2,k3,k4,k5,k6,k7 = st.columns(7)
k1.metric("💰 MRR", f"${total_mrr:,}")
k2.metric("📈 ARR", f"${total_mrr*12:,}")
k3.metric("👥 Customers", total_customers)
k4.metric("📦 Live Products", sum(1 for p in products if p["status"]=="Live"))
k5.metric("🎭 Avatars", len(avatars))
k6.metric("🔍 Leads", len(leads))
k7.metric("📋 Tasks", len(pending_tasks))
st.markdown("<hr style='border-color:#0f0f0f;margin:8px 0 0 0;'>", unsafe_allow_html=True)

# ── TABS ──────────────────────────────────────────────────────────────────────
tabs = st.tabs([
    "🏠 Command","💬 AI Chat","🤖 Agents","🎭 Avatar Builder",
    "📧 Email Suite","🔍 Lead Scraper","📦 Products","💰 Revenue",
    "🎙️ Podcast","🌐 Web Tools","🚀 Business Tools","📋 Task Sheet","⚙️ Settings"
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 0 — COMMAND CENTRE
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    st.markdown("## 🏠 Daily Command Centre")
    col1, col2 = st.columns([1.5, 1])

    with col1:
        st.markdown("### 📋 Morning Briefing")
        st.markdown(f"""<div class='card card-g'>
<p style='margin:4px 0;'>📅 <strong>Today:</strong> {now.strftime('%A %d %B %Y')}</p>
<p style='margin:4px 0;'>💰 <strong>MRR:</strong> <span style='color:#00ff41;'>${total_mrr:,}</span> &nbsp;|&nbsp; ARR: <span style='color:#00ff41;'>${total_mrr*12:,}</span></p>
<p style='margin:4px 0;'>✅ <strong>Done today:</strong> {len(done_today)} &nbsp;|&nbsp; ⏳ Pending: {len(pending_tasks)}</p>
<p style='margin:4px 0;'>🎭 <strong>Avatars:</strong> {len(avatars)} &nbsp;|&nbsp; 👥 Leads: {len(leads)} &nbsp;|&nbsp; 🏆 Wins: {len(wins)}</p>
<p style='margin:4px 0;'>📦 <strong>Live:</strong> {sum(1 for p in products if p["status"]=="Live")} products &nbsp;|&nbsp; 👥 Customers: {total_customers}</p>
</div>""", unsafe_allow_html=True)

        st.markdown("### ⚡ Quick Actions")
        qa1,qa2,qa3,qa4 = st.columns(4)
        with qa1:
            if st.button("📧 Email Suite", use_container_width=True): st.info("→ Email Suite tab")
        with qa2:
            if st.button("🎭 Build Avatar", use_container_width=True): st.info("→ Avatar Builder tab")
        with qa3:
            if st.button("🔍 Scrape Leads", use_container_width=True): st.info("→ Lead Scraper tab")
        with qa4:
            if st.button("🔔 Notify Phone", use_container_width=True):
                msg = f"""🎭 <b>Avatar Empire Briefing</b>
📅 {now.strftime('%d %b %Y %H:%M')}
💰 MRR: ${total_mrr:,} | ARR: ${total_mrr*12:,}
📋 Pending tasks: {len(pending_tasks)}
👥 Leads: {len(leads)} | Avatars: {len(avatars)}
📦 Live products: {sum(1 for p in products if p["status"]=="Live")}"""
                sent = send_telegram(msg)
                st.success("Sent to Telegram!" if sent else "Add Telegram token in Settings.")

        st.markdown("### ➕ Quick Task")
        with st.form("quick_task"):
            qt = st.text_input("Task:", placeholder="e.g. Follow up with 3 mining leads")
            qp = st.selectbox("Priority:", ["🔴 High","🟡 Medium","🟢 Low"])
            if st.form_submit_button("Add Task"):
                tasksheet.append({"task":qt,"priority":qp,"done":False,
                                   "date":now.strftime("%Y-%m-%d"),"added":now.strftime("%H:%M"),"category":"Quick"})
                jsave(TASKF, tasksheet); st.success("Added!"); st.rerun()

        if st.button("🤖 Generate AI Daily Plan", use_container_width=True):
            result, engine = ai_call(
                f"It's {now.strftime('%A %d %B')}. I run an AI tools business. MRR: ${total_mrr:,}. "
                f"Leads: {len(leads)}. Pending tasks: {len(pending_tasks)}. "
                f"Live products: {sum(1 for p in products if p['status']=='Live')}. "
                "Give me a sharp, prioritised 8-item action plan for today. Numbered list. Be specific.",
                system="You are a no-BS business coach. Give sharp, specific daily action plans.", max_tokens=500)
            if result:
                st.markdown(f"""<div class='card card-g'><pre style='white-space:pre-wrap;color:#e0e0e0;font-family:Inter,sans-serif;font-size:.88em;'>{result}</pre></div>""", unsafe_allow_html=True)
                lines = [re.sub(r'^\d+[\.\)]\s*','',l.strip()) for l in result.split("\n") if l.strip() and l.strip()[0].isdigit()]
                for line in lines[:8]:
                    if line: tasksheet.append({"task":line,"priority":"🟡 Medium","done":False,"date":now.strftime("%Y-%m-%d"),"added":now.strftime("%H:%M"),"category":"AI Plan"})
                jsave(TASKF, tasksheet)
            else: st.warning("No AI engine — start LM Studio or add OpenAI key in Settings.")

    with col2:
        st.markdown("### 📊 Revenue Milestones")
        for label, target in [("$5K MRR",5000),("$10K MRR",10000),("$25K MRR",25000),("$50K MRR",50000),("$100K MRR",100000)]:
            pct = min(total_mrr/target, 1.0)
            col = "#00ff41" if pct>=1.0 else "#ffd700" if pct>0.5 else "#ff0080"
            st.markdown(f"<span style='color:{col};font-weight:700;font-size:.9em;'>{label}</span> {'✅' if pct>=1.0 else f'— {pct*100:.0f}%'}", unsafe_allow_html=True)
            st.progress(pct)

        st.markdown("### 🚀 Projections")
        for m, r in [("Month 1","$3K–$5K"),("Month 3","$12K–$15K"),("Month 6","$25K–$30K"),("Month 12","$50K+")]:
            st.markdown(f"<span style='color:#333;font-size:.85em;'>{m}:</span> <strong style='color:#00ff41;'>{r} MRR</strong>", unsafe_allow_html=True)

        st.markdown("### 🏆 Weekly Wins")
        win_text = st.text_input("Log a win:", placeholder="e.g. Closed first paying customer!")
        if st.button("🏆 Log Win", use_container_width=True):
            if win_text.strip():
                wins.append({"win":win_text,"date":now.strftime("%Y-%m-%d"),"time":now.strftime("%H:%M")})
                jsave(WINSF, wins); st.success("Win logged! 🔥"); st.rerun()
        for w in reversed(wins[-5:]):
            st.markdown(f"<span style='color:#ffd700;'>🏆</span> {w['win']} <span style='color:#222;font-size:.75em;'>{w.get('date','')}</span>", unsafe_allow_html=True)

        st.markdown("### 🎯 Unfair Advantages")
        for adv in ["10 years business experience","Renovation/construction expertise","Warm tradie network","Sales skills — closed $50K+ deals","Understanding of real pain points","All-in mentality"]:
            st.markdown(f"<span style='color:#00ff41;font-size:.85em;'>✓</span> <span style='font-size:.85em;'>{adv}</span>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — AI CHAT
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    st.markdown("## 💬 AI Command Chat")
    st.markdown("<p style='color:#555;font-size:.85em;'>Your AI crew in one chat window. Assign tasks, get reports, write content, build strategies. Powered by your local Llama-3.2 via LM Studio — works offline.</p>", unsafe_allow_html=True)

    _, engine_test = ai_call("ping", system="Reply with just: pong", max_tokens=5)
    if "Offline" in engine_test or "Error" in engine_test:
        st.markdown('<span class="pill-off">⚡ No AI Engine — Start LM Studio or add OpenAI key in Settings</span>', unsafe_allow_html=True)
    else:
        st.markdown(f'<span class="pill-ai">⚡ {engine_test}</span>', unsafe_allow_html=True)

    st.markdown("---")

    # Chat history
    if not chat_hist:
        st.markdown("""<div class='chat-sys'>
👋 <strong>Welcome to AI Command Chat.</strong> I know your business — products, revenue, leads, tasks, agents.<br>
Try: <em>"Write a cold email for a mining company"</em> · <em>"What's my MRR?"</em> · <em>"Build a TikTok script for a plumbing avatar"</em> · <em>"Give me today's action plan"</em> · <em>"Write a proposal for a $2,000 client"</em>
</div>""", unsafe_allow_html=True)
    else:
        for msg in chat_hist[-25:]:
            if msg["role"] == "user":
                st.markdown(f"<div class='chat-user'><strong style='color:#00ff41;font-size:.8em;'>YOU · {msg.get('time','')}</strong><br>{msg['content']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='chat-ai'><strong style='color:#ff0080;font-size:.8em;'>AGENT · {msg.get('engine','AI')} · {msg.get('time','')}</strong><br><pre style='white-space:pre-wrap;font-family:Inter,sans-serif;margin:6px 0 0 0;color:#ddd;font-size:.88em;'>{msg['content']}</pre></div>", unsafe_allow_html=True)

    st.markdown("---")

    # Quick commands
    st.markdown("<span style='color:#333;font-size:.8em;'>QUICK COMMANDS:</span>", unsafe_allow_html=True)
    qc1,qc2,qc3,qc4,qc5,qc6 = st.columns(6)
    quick_cmd = ""
    with qc1:
        if st.button("📊 MRR Report", use_container_width=True):
            quick_cmd = f"Revenue report: MRR ${total_mrr:,}, ARR ${total_mrr*12:,}. Products: {', '.join([p['name']+' $'+str(p.get('mrr',0)) for p in products if p.get('mrr',0)>0])}. What should I focus on to grow MRR fastest?"
    with qc2:
        if st.button("📧 Cold Email", use_container_width=True):
            quick_cmd = "Write a high-converting cold email for a small business owner about AI tools. Punchy, Australian tone, under 150 words, strong CTA."
    with qc3:
        if st.button("📋 Today's Plan", use_container_width=True):
            quick_cmd = f"It's {now.strftime('%A')}. AI tools business. MRR ${total_mrr:,}. {len(leads)} leads. {len(pending_tasks)} pending tasks. Give me a sharp prioritised action plan for today."
    with qc4:
        if st.button("🎭 Avatar Idea", use_container_width=True):
            quick_cmd = "Give me 3 fresh avatar niche ideas for TikTok/YouTube targeting Australian audiences. Include monetisation potential for each."
    with qc5:
        if st.button("💡 Business Idea", use_container_width=True):
            quick_cmd = "Give me one killer AI business idea I can build and sell in 30 days. Specific: niche, price, target customer, how to get first 10 sales."
    with qc6:
        if st.button("💰 Close Script", use_container_width=True):
            quick_cmd = "Write a word-for-word sales closing script for selling a $297/month AI tool to a small business owner who said 'I need to think about it'."

    # Input form
    with st.form("chat_form", clear_on_submit=True):
        ci, cb = st.columns([5, 1])
        with ci:
            user_input = st.text_input("", placeholder="Ask anything, assign a task, or give a command...", label_visibility="collapsed")
        with cb:
            send = st.form_submit_button("Send ➤", use_container_width=True)

    if quick_cmd:
        user_input = quick_cmd; send = True

    if send and user_input.strip():
        system_ctx = f"""You are the Avatar Empire AI Command Centre — a sharp, direct, no-BS business AI.
Business context: MRR ${total_mrr:,} | ARR ${total_mrr*12:,} | {len(products)} products ({sum(1 for p in products if p['status']=='Live')} live) | {len(leads)} leads | {len(avatars)} avatars | {len(pending_tasks)} pending tasks | Date: {now.strftime('%A %d %B %Y')}
You are Australian, direct, practical, focused on making money. When asked to write content, write it fully. When asked for a plan, give specific actions. Keep responses sharp and actionable."""
        chat_hist.append({"role":"user","content":user_input,"time":now.strftime("%H:%M")})
        with st.spinner("Agent thinking..."):
            result, engine = ai_call(user_input, system=system_ctx, max_tokens=900)
        chat_hist.append({"role":"assistant","content":result or "No AI engine. Start LM Studio or add OpenAI key in Settings.","engine":engine,"time":now.strftime("%H:%M")})
        jsave(CF, chat_hist[-80:])
        st.rerun()

    col_clr1, col_clr2 = st.columns([5, 1])
    with col_clr2:
        if st.button("🗑️ Clear"):
            jsave(CF, []); st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — AGENT SQUAD
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    st.markdown("## 🤖 AI Agent Crew")
    AGENTS = [
        {"name":"Content Machine","role":"Scripts, posts, captions, blogs, ad copy","icon":"✍️","color":"card-g",
         "system":"You are Content Machine, expert content creator. Write compelling, platform-specific content that drives engagement and sales. Be specific, punchy, Australian tone."},
        {"name":"Email Agent","role":"Cold emails, follow-ups, sequences, replies","icon":"📧","color":"card-p",
         "system":"You are Email Agent, expert email copywriter. Write emails that get opened, read, and actioned. Australian tone, direct, no fluff. Always include subject line."},
        {"name":"Sales Bot","role":"Lead qualification, objection handling, proposals","icon":"💬","color":"card-b",
         "system":"You are Sales Bot, expert sales closer. Handle objections, qualify leads, write proposals, close deals. Be direct and confident."},
        {"name":"Analytics Brain","role":"Data insights, revenue reports, projections","icon":"📊","color":"card-y",
         "system":"You are Analytics Brain, data analyst. Provide sharp, actionable insights from business data. Be specific with numbers and recommendations."},
        {"name":"Deploy Master","role":"Launch products, automations, workflows","icon":"🚀","color":"card-g",
         "system":"You are Deploy Master, expert in launching digital products. Provide step-by-step deployment plans. Be practical and specific."},
        {"name":"Code Builder","role":"Write, fix, and optimise production code","icon":"💻","color":"card-p",
         "system":"You are Code Builder, expert Python/web developer. Write clean, production-ready code with clear explanations."},
    ]

    col_a, col_b = st.columns(2)
    for i, agent in enumerate(AGENTS):
        col = col_a if i % 2 == 0 else col_b
        with col:
            st.markdown(f"""<div class='card {agent["color"]}'><h3 style='margin:0 0 2px 0;font-size:1em;'>{agent["icon"]} {agent["name"]}</h3>
<p style='color:#555;margin:0 0 4px 0;font-size:.82em;'>{agent["role"]}</p>
<span style='color:#00ff41;font-size:.75em;font-weight:700;'>🟢 ONLINE</span></div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### ⚡ Assign Task to Agent")
    col1, col2 = st.columns([2, 1])
    with col1:
        task_desc = st.text_area("Task:", height=80, placeholder="e.g. Write 5 TikTok scripts for a plumbing avatar targeting homeowners aged 30-55 in Sydney...")
    with col2:
        agent_sel = st.selectbox("Agent:", ["Auto-Select"] + [a["name"] for a in AGENTS])
        priority  = st.selectbox("Priority:", ["🔴 High","🟡 Medium","🟢 Low"])

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🚀 Execute Now", use_container_width=True, type="primary"):
            if task_desc.strip():
                assigned = agent_sel if agent_sel != "Auto-Select" else "Content Machine"
                agent_sys = next((a["system"] for a in AGENTS if a["name"] == assigned), AGENTS[0]["system"])
                new_task = {"id":len(tasks)+1,"desc":task_desc,"agent":assigned,"priority":priority,
                            "status":"Running","date":now.strftime("%Y-%m-%d"),"time":now.strftime("%H:%M")}
                tasks.append(new_task); jsave(TF, tasks)
                with st.spinner(f"{assigned} executing..."):
                    result, engine = ai_call(task_desc, system=agent_sys, max_tokens=1000)
                if result:
                    tasks[-1]["result"] = result; tasks[-1]["status"] = "Done"; tasks[-1]["engine"] = engine
                    jsave(TF, tasks)
                    st.success(f"✅ {assigned} completed — via {engine}")
                    st.markdown(f"""<div class='card card-g'><pre style='white-space:pre-wrap;color:#e0e0e0;font-family:Inter,sans-serif;font-size:.88em;'>{result}</pre></div>""", unsafe_allow_html=True)
                    send_telegram(f"✅ Agent Task Done\n{assigned}: {task_desc[:80]}")
                else:
                    tasks[-1]["status"] = "Queued"; jsave(TF, tasks)
                    st.warning("No AI engine — task queued. Start LM Studio or add OpenAI key.")
            else: st.warning("Describe the task first.")
    with c2:
        if st.button("📋 Queue Task", use_container_width=True):
            if task_desc.strip():
                tasks.append({"id":len(tasks)+1,"desc":task_desc,"agent":agent_sel,"priority":priority,
                              "status":"Queued","date":now.strftime("%Y-%m-%d"),"time":now.strftime("%H:%M")})
                jsave(TF, tasks); st.success("Queued!")
    with c3:
        if st.button("🗑️ Clear Queue", use_container_width=True):
            jsave(TF, []); st.success("Cleared."); st.rerun()

    st.markdown("---")
    st.markdown("### 📋 Daily Agent Assignment Sheet")
    DAILY_TASKS = {
        "✍️ Content Machine":["Write 3 LinkedIn posts","Draft newsletter for Friday","Create ad copy for top product","Write 5 TikTok scripts"],
        "📧 Email Agent":["Send cold outreach batch (10 emails)","Follow up on unanswered emails","Draft onboarding sequence for new customers"],
        "💬 Sales Bot":["Respond to all inquiries within 1 hour","Follow up with trial users","Send proposals to warm leads"],
        "📊 Analytics Brain":["Generate weekly revenue report","Analyse customer churn","Identify top-performing products"],
        "🚀 Deploy Master":["Deploy latest updates","Test all products in production","Monitor uptime and performance"],
        "💻 Code Builder":["Build new feature for Email Assassin","Fix any reported bugs","Review and optimise existing code"],
    }
    for agent_name, daily in DAILY_TASKS.items():
        with st.expander(f"📌 {agent_name}"):
            for dt in daily:
                col_dt, col_run = st.columns([4, 1])
                with col_dt: st.markdown(f"- {dt}")
                with col_run:
                    if st.button("▶", key=f"run_{agent_name}_{dt}"):
                        clean_name = agent_name.split(" ",1)[1] if " " in agent_name else agent_name
                        agent_sys = next((a["system"] for a in AGENTS if a["name"]==clean_name), AGENTS[0]["system"])
                        with st.spinner("Running..."):
                            result, engine = ai_call(dt, system=agent_sys, max_tokens=600)
                        if result:
                            st.text_area("Result:", value=result, height=150, key=f"res_{agent_name}_{dt}")

    if tasks:
        st.markdown("---")
        st.markdown("### 📋 Task Queue")
        for t in reversed(tasks[-10:]):
            sc = "#00ff41" if t.get("status")=="Done" else "#ffd700" if t.get("status")=="Running" else "#555"
            st.markdown(f"""<div class='card'><span style='color:{sc};font-weight:700;font-size:.8em;'>[{t.get("status","?")}]</span> <strong style='font-size:.88em;'>{t.get("agent","?")}</strong> — <span style='font-size:.85em;'>{t.get("desc","")[:80]}</span> <span style='color:#222;float:right;font-size:.72em;'>{t.get("date","")} {t.get("time","")}</span></div>""", unsafe_allow_html=True)
            if t.get("result"):
                with st.expander(f"View result"):
                    st.text(t["result"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — AVATAR BUILDER
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    st.markdown("## 🎭 Autonomous Avatar Builder")
    st.markdown("<p style='color:#555;font-size:.85em;'>Drop in your idea — the AI builds the entire avatar to completion. Bio, scripts, content strategy, monetisation plan, platform setup. You direct, the agent executes.</p>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        av_name     = st.text_input("Avatar Name:", "Mike Thompson")
        av_niche    = st.selectbox("Niche:", ["Plumbing & Home Repair","Electrical","HVAC","Woodworking","Fitness & Health","Cooking & Food","Finance & Investing","Tech Reviews","Real Estate","Cybersecurity","Mining & Trades","Landscaping","Cleaning & Maintenance","Custom..."])
        if av_niche == "Custom...": av_niche = st.text_input("Custom niche:")
        av_idea     = st.text_area("Your idea / rough concept:", height=80, placeholder="e.g. Funny plumber in Sydney, targets homeowners, wants to sell a $97 DIY course. TikTok + YouTube.")
        av_target   = st.text_input("Target audience:", "Homeowners aged 30–55, DIY enthusiasts")
    with col2:
        av_platforms= st.multiselect("Platforms:", ["YouTube","TikTok","Instagram","Twitter/X","Blog","Podcast","Email List","LinkedIn"], default=["YouTube","TikTok"])
        av_goal     = st.slider("Monthly Revenue Goal ($):", 1000, 100000, 30000, step=1000)
        av_voice    = st.selectbox("Voice Style:", ["Warm & Friendly","Professional","Energetic & Hype","Calm & Relaxed","Authoritative Expert","Funny & Relatable","Aussie Larrikin"])
        av_monetise = st.multiselect("Monetisation:", ["Ad Revenue","Affiliate Links","Digital Products","Coaching/Consulting","Sponsorships","Online Courses","Merchandise","Services"], default=["Ad Revenue","Digital Products","Affiliate Links"])

    st.markdown("---")
    if st.button("🚀 BUILD FULL AVATAR — AI Does Everything", use_container_width=True, type="primary"):
        prompt = f"""Build a COMPLETE, ready-to-deploy autonomous avatar for:
Name: {av_name} | Niche: {av_niche} | Concept: {av_idea}
Target: {av_target} | Platforms: {', '.join(av_platforms)} | Revenue Goal: ${av_goal:,}/mo
Voice: {av_voice} | Monetisation: {', '.join(av_monetise)}

Deliver ALL of the following — fully written, not described:

## 1. AVATAR PROFILE
Full bio (2 paragraphs), tagline, brand voice guide, posting schedule

## 2. CONTENT STRATEGY
5 content pillars with 3 post ideas each

## 3. SCRIPTS (write them in full)
- 3 x TikTok/Reels scripts (60 seconds each, include hooks)
- 2 x YouTube video outlines (5-7 min, with intro/sections/outro)
- 5 x post captions ready to copy-paste

## 4. MONETISATION ROADMAP
Month 1, 3, 6, 12 — specific revenue targets and actions to hit them

## 5. PLATFORM SETUP CHECKLIST
Step-by-step for each selected platform

## 6. FIRST 30 DAYS ACTION PLAN
Week 1 day-by-day, Weeks 2-4 weekly

## 7. PRODUCT IDEAS
3 digital products this avatar could sell, with pricing and sales copy

Be specific. Write everything in full. This person executes today."""

        with st.spinner(f"Building {av_name}'s complete avatar empire..."):
            result, engine = ai_call(prompt, system=f"You are an expert avatar strategist and content creator. Build complete, fully-written, immediately executable avatar empires. Voice: {av_voice}. Niche: {av_niche}.", max_tokens=2500)

        if result:
            avatars.append({"name":av_name,"niche":av_niche,"platforms":av_platforms,"goal":av_goal,
                             "voice":av_voice,"monetise":av_monetise,"idea":av_idea,
                             "created":now.strftime("%Y-%m-%d %H:%M"),"profile":result,"engine":engine})
            jsave(AVF, avatars)
            st.success(f"✅ {av_name} built via {engine}!")
            st.markdown(f"""<div class='card card-g'><pre style='white-space:pre-wrap;color:#e0e0e0;font-family:Inter,sans-serif;font-size:.85em;'>{result}</pre></div>""", unsafe_allow_html=True)
            send_telegram(f"🎭 Avatar Built: {av_name} | {av_niche} | Goal: ${av_goal:,}/mo")
        else:
            st.warning("No AI engine — start LM Studio or add OpenAI key in Settings.")

    st.markdown("---")
    st.markdown("### 🎭 Magic Mike System — Checklist")
    mike_items = ["Create avatar character & name","Generate voice profile (ElevenLabs)","Write first 10 scripts","Create first 5 videos","Set up YouTube channel","Set up TikTok account","Set up Instagram account","Configure auto-posting tool","Test full workflow end-to-end","Launch and monitor analytics"]
    for item in mike_items:
        st.checkbox(item, key=f"mike_{item}")

    if avatars:
        st.markdown("---")
        st.markdown(f"### 🎭 Your Avatar Roster ({len(avatars)} built)")
        for av in reversed(avatars):
            with st.expander(f"🎭 {av['name']} — {av['niche']} ({av.get('created','')})"):
                st.markdown(f"**Platforms:** {', '.join(av.get('platforms',[]))} | **Goal:** ${av.get('goal',0):,}/mo | **Engine:** {av.get('engine','')}")
                if st.button(f"📄 View Full Profile", key=f"avp_{av['name']}_{av.get('created','')}"):
                    st.text_area("Profile:", value=av.get("profile",""), height=400, key=f"avt_{av['name']}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — EMAIL SUITE
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[4]:
    st.markdown("## 📧 Email Suite")
    et1, et2, et3, et4 = st.tabs(["📝 All 20 Templates","🤖 AI Auto-Reply","✉️ AI Email Writer","📅 Drip Sequences"])

    with et1:
        st.markdown("### 📝 All 20 Ready-to-Send Templates")
        TEMPLATES = {
            "1. Cold Outreach — Mining/SOCI Act": {
                "subject": "SOCI Act compliance in 5 minutes instead of 5 weeks",
                "body": "G'day [Name],\n\nQuick question about [Company]'s cybersecurity compliance.\n\nAre you spending weeks preparing SOCI Act reports for the board?\n\nI've built an AI system that generates compliance documentation in minutes instead of months. Risk assessments, incident reports, gap analyses - all automated.\n\nFormer A&I Armour engineer. Worked with [mention any mutual connection or similar company].\n\nWorth a 15-minute call to show you how [Company X] cut their compliance overhead by 80%?\n\nAvailable Tuesday or Thursday this week.\n\nCheers,\n[Your Name]\n[Phone]"
            },
            "2. Warm Follow-Up — Tradies": {
                "subject": "That admin tool I mentioned",
                "body": "Hey [Name],\n\nRemember you said quoting takes you 2+ hours per job?\n\nI built the thing I was talking about - AI generates professional quotes in 2 minutes.\n\nYou type: \"Kitchen reno, replace taps, fix leak\"\nIt outputs: Full itemized quote with pricing, scope, timeline, T&Cs\n\nAlready saving [Mate's Name] 10+ hours per week.\n\n$197/month. Try it free for a week?\n\nLet me know - I'll set you up today.\n\nCheers,\n[Your Name]"
            },
            "3. LinkedIn Outreach — B2B": {
                "subject": "[Name] - Quick AI question",
                "body": "Hi [Name],\n\nSaw your post about [relevant topic].\n\nBuilt an AI tool that [solves specific problem]. Thought you might be interested given your work at [Company].\n\n[One-sentence description of tool]\n\nNot pitching - genuinely think this could help your team. Happy to show you a quick demo if you're curious.\n\n5 minutes on Zoom?\n\nCheers,\n[Your Name]"
            },
            "4. Follow-Up After Demo": {
                "subject": "Re: AI Email Assassin demo",
                "body": "[Name],\n\nThanks for jumping on the call yesterday.\n\nAs discussed, AI Email Assassin would save your team ~15 hours per week on email responses.\n\nQuick recap:\n• Paste email → AI drafts response in 10 seconds\n• $97/month for unlimited use\n• 7-day free trial (no credit card)\n\nNext steps:\n1. Try it this week (link below)\n2. Quick check-in Friday\n3. If it works, convert to paid\n\nTrial link: [URL]\n\nQuestions? Just reply to this.\n\nCheers,\n[Your Name]"
            },
            "5. Objection Handler — Price": {
                "subject": "Re: Pricing question",
                "body": "[Name],\n\nFair question on the $697/month for Lead Generator.\n\nQuick math:\n\nYour sales team spends ~20 hours/week finding leads manually.\nThat's 80 hours/month.\n\nAt $50/hour = $4,000 in labor costs.\n\nLead Generator:\n• Finds 100+ qualified leads/month\n• Auto-generates outreach\n• Tracks responses\n• Costs $697\n\nSo you save $3,303/month while getting better leads.\n\nPlus if you close even ONE extra deal from those leads, it pays for itself 10x over.\n\nMake sense?\n\nHappy to do a 1-month trial at 50% off ($348) so you can prove ROI before committing.\n\nKeen?\n\nCheers,\n[Your Name]"
            },
            "6. Welcome — New Customer": {
                "subject": "Welcome to [Product Name]! Here's how to get started",
                "body": "Hey [Name]!\n\nStoked to have you on board with [Product Name]. 🎉\n\nHere's your getting started guide:\n\nStep 1: Login\nURL: [link]\nEmail: [their email]\nPassword: Check your separate email\n\nStep 2: Try your first [task]\n[Quick win instructions - 3 steps max]\n\nStep 3: Watch this 2-min tutorial\n[Video link]\n\nNeed help?\nReply to this email or book a call: [calendar link]\n\nCommon questions:\n• [FAQ 1 with answer]\n• [FAQ 2 with answer]\n\nLet's crush it!\n\n[Your Name]\n[Support email]\n[Phone]"
            },
            "7. Day 3 Check-In": {
                "subject": "How's [Product] working for you?",
                "body": "Hey [Name],\n\n3 days in - wanted to check how [Product] is treating you.\n\nQuick questions:\n1. Have you [completed key action]?\n2. Any issues or confusion?\n3. What would make this better for you?\n\nHit reply and let me know. I read every response.\n\nAlso, pro tip: [specific feature they might not have discovered]\n\nCheers,\n[Your Name]"
            },
            "8. Renewal Reminder": {
                "subject": "Your [Product] subscription renews in 3 days",
                "body": "Hey [Name],\n\nQuick heads up - your [Product Name] subscription renews on [date].\n\nThis month you:\n• [Stat 1 - tasks completed]\n• [Stat 2 - time saved]\n• [Stat 3 - value delivered]\n\nRenewal: $[amount] on [date]\n\nAll good to continue? You don't need to do anything - it'll auto-renew.\n\nWant to cancel or have questions? Just reply.\n\nCheers,\n[Your Name]"
            },
            "9. Feature Update": {
                "subject": "New feature just for you 🎁",
                "body": "Hey [Name],\n\nJust shipped something you're going to love.\n\n[Product Name] now has [new feature].\n\nWhat it does:\n[Benefit in one sentence]\n\nHow to use it:\n1. [Step 1]\n2. [Step 2]\n3. [Step 3]\n\nThis was our most-requested feature. Thanks for the feedback.\n\nTry it out and let me know what you think!\n\nCheers,\n[Your Name]"
            },
            "10. Win-Back — Churned Customer": {
                "subject": "We miss you at [Product Name]",
                "body": "Hey [Name],\n\nNoticed you cancelled [Product Name] last month.\n\nNo hard feelings - but I'm curious what happened.\n\nWas it:\n• Price?\n• Missing features?\n• Didn't see value?\n• Just didn't need it anymore?\n\nQuick 2-minute call? I'd love to understand what went wrong so we can improve.\n\nPlus, if you're willing to give us another shot, I'll comp you a month free to try the new features we've added.\n\nNo pressure either way.\n\nCheers,\n[Your Name]"
            },
            "11. Partnership / Collaboration Pitch": {
                "subject": "Partnership idea for [Their Company]",
                "body": "Hey [Name],\n\nLove what you're doing with [Their Company].\n\nI built [Your Product] which helps [their audience] with [problem].\n\nThought we could collaborate:\n\nOption 1: Affiliate partnership\nYou promote to your audience, earn 20% recurring commission.\n\nOption 2: Co-marketing\nJoint webinar, share audiences, both benefit.\n\nOption 3: Integration\n[Your Product] + [Their Product] = better solution for customers.\n\nInterested in exploring any of these?\n\n15-min call to discuss?\n\nCheers,\n[Your Name]"
            },
            "12. Guest Post Pitch": {
                "subject": "Article idea for [Their Blog]",
                "body": "Hey [Name],\n\nRegular reader of [Their Blog]. Loved your recent post on [topic].\n\nI'd like to contribute an article:\n\nTitle: \"[Specific, valuable title]\"\n\nWhy your audience will love it:\n[Benefit 1]\n[Benefit 2]\n[Benefit 3]\n\nMy credentials:\n[Relevant experience/expertise]\n\nNot promoting anything - just want to provide value to your readers.\n\nInterested?\n\nCheers,\n[Your Name]"
            },
            "13. Bug Report Response": {
                "subject": "Re: [Bug description]",
                "body": "Hey [Name],\n\nThanks for reporting this. Sorry you're experiencing [issue].\n\nWhat's happening:\nI've logged this as a priority bug. Our team is investigating.\n\nTemporary workaround:\n[If applicable - steps to work around the issue]\n\nTimeline:\nWe'll have a fix deployed by [date/time].\n\nI'll update you as soon as it's resolved.\n\nAppreciate your patience!\n\nCheers,\n[Your Name]\n[Support ticket #]"
            },
            "14. Feature Request Response": {
                "subject": "Re: Feature request - [Feature name]",
                "body": "Hey [Name],\n\nLove this idea for [Feature].\n\nGood news: This is already on our roadmap for [timeframe].\n\nI've added your vote to the request and cc'd you on the development ticket. You'll get updates as we build it.\n\nIn the meantime, [alternative solution if available].\n\nThanks for making [Product] better!\n\nCheers,\n[Your Name]"
            },
            "15. Daily Agent Task Assignment": {
                "subject": "Agent Tasks - [Date]",
                "body": "Agent Squad,\n\nToday's priorities:\n\nCode Builder:\n- [ ] Build [feature] for [product]\n- [ ] Fix bug in [product]\n- [ ] Review PR #47\n\nContent Machine:\n- [ ] Write ad copy for [product launch]\n- [ ] Create 3 LinkedIn posts\n- [ ] Draft newsletter for Friday\n\nDeploy Master:\n- [ ] Deploy [product] to Streamlit Cloud\n- [ ] Test [feature] in production\n- [ ] Monitor uptime\n\nSales Bot:\n- [ ] Respond to 12 inquiries\n- [ ] Follow up with [customer]\n- [ ] Send proposal to [prospect]\n\nAnalytics Brain:\n- [ ] Generate weekly revenue report\n- [ ] Analyse customer churn data\n- [ ] Identify top-performing products\n\nAll due EOD.\n\nGo!"
            },
            "16. Testimonial Request": {
                "subject": "Quick favor? 2-minute testimonial",
                "body": "Hey [Name],\n\nYou've been using [Product] for [timeframe] now and I'm seeing great results on your account.\n\nWould you be willing to share a quick testimonial?\n\nJust answer these 3 questions:\n1. What problem were you trying to solve?\n2. How has [Product] helped?\n3. What results have you seen?\n\n2-3 sentences total. That's it.\n\nI'll use it on the website (with your permission) to help others like you find the solution.\n\nHappy to return the favor anytime!\n\nCheers,\n[Your Name]"
            },
            "17. Referral Request": {
                "subject": "Know anyone who needs [solution]?",
                "body": "Hey [Name],\n\nQuick question: Do you know anyone else struggling with [problem that your product solves]?\n\nI'm opening up 5 spots for new customers this month and thought you might know someone who'd benefit.\n\nReferral bonus:\nFor each person you refer who becomes a customer, you get:\n• $100 credit to your account\n• They get 50% off first month\n\nJust forward this email or send me their details.\n\nWin-win!\n\nCheers,\n[Your Name]"
            },
            "18. Upsell — Upgrade to Pro": {
                "subject": "Ready to level up? Pro features unlocked",
                "body": "Hey [Name],\n\nYou've been crushing it with [Product Name] Starter.\n\nStats:\n• [Metric 1]\n• [Metric 2]\n• [Metric 3]\n\nYou're hitting the limits of Starter plan.\n\nUpgrade to Pro and get:\n• [Feature 1]\n• [Feature 2]\n• [Feature 3]\n• Priority support\n\nJust $[price difference more]/month.\n\nWant to try Pro free for 7 days?\n\nClick here: [upgrade link]\n\nCheers,\n[Your Name]"
            },
            "19. Inactive User Nudge": {
                "subject": "We miss you at [Product Name]!",
                "body": "Hey [Name],\n\nHaven't seen you in [Product Name] for a couple weeks.\n\nEverything okay?\n\nJust a reminder of what's waiting for you:\n• [Feature 1]\n• [Feature 2]\n• [New thing they haven't tried]\n\nPlus we just added: [new feature]\n\nTakes 2 minutes to jump back in: [login link]\n\nNeed help getting started again? Hit reply.\n\nCheers,\n[Your Name]"
            },
            "20. Weekly Newsletter": {
                "subject": "This Week in [Your Niche] + Product Updates",
                "body": "Hey [Name],\n\nQuick hits from this week:\n\n🔥 What's New:\n• [Product update or new feature]\n• [Industry news relevant to audience]\n• [Customer win/case study]\n\n💡 Tip of the Week:\n[One actionable tip related to your product - 2-3 sentences]\n\n📊 By the Numbers:\n• [Interesting stat 1]\n• [Interesting stat 2]\n\n🎯 Coming Soon:\n[Tease upcoming feature or content]\n\nThat's it! See you next week.\n\nCheers,\n[Your Name]\n\nP.S. [One-liner CTA or fun fact]"
            },
        }

        selected_tpl = st.selectbox("Choose template:", list(TEMPLATES.keys()))
        tpl = TEMPLATES[selected_tpl]
        st.markdown(f"**Subject:** `{tpl['subject']}`")
        edited = st.text_area("Email body (edit as needed):", value=tpl["body"], height=280)
        col_copy, col_ai = st.columns(2)
        with col_copy:
            if st.button("📋 Copy-Ready Format"):
                st.code(f"Subject: {tpl['subject']}\n\n{edited}")
        with col_ai:
            if st.button("🤖 AI-Personalise This Template"):
                context = st.text_input("Who is this for? (brief context):", placeholder="e.g. Mining company in Perth, 50 staff, compliance issues", key="tpl_ctx")
                if context:
                    result, engine = ai_call(f"Personalise this email template for: {context}\n\nTemplate:\nSubject: {tpl['subject']}\n\n{edited}\n\nFill in all [brackets] with specific, realistic details. Keep the same structure.", system="You are an expert email copywriter.", max_tokens=500)
                    if result: st.text_area("Personalised:", value=result, height=250)

    with et2:
        st.markdown("### 🤖 AI Auto-Reply Generator")
        received = st.text_area("Paste the email you received:", height=150, placeholder="Paste the full email here...")
        c1, c2 = st.columns(2)
        with c1: tone = st.selectbox("Reply tone:", ["Professional","Friendly & Warm","Direct & Concise","Apologetic","Sales-Focused","Australian Casual"])
        with c2: goal = st.selectbox("Goal:", ["Book a Call","Close the Sale","Handle Objection","Provide Information","Confirm / Acknowledge","Follow Up"])
        if st.button("🤖 Generate Reply", use_container_width=True, type="primary"):
            if received.strip():
                result, engine = ai_call(
                    f"You received this email:\n---\n{received}\n---\nWrite a reply. Tone: {tone}. Goal: {goal}. Be concise, human, include clear CTA. Australian tone. Just the email body, no subject line.",
                    system="You are an expert email copywriter. Write replies that get results.", max_tokens=450)
                if result: st.text_area("Your reply:", value=result, height=200)
                else: st.warning("No AI engine available.")
            else: st.warning("Paste an email first.")

    with et3:
        st.markdown("### ✉️ AI Email Writer")
        ew_purpose   = st.text_input("What's this email for?", placeholder="e.g. Cold outreach to a mortgage broker about my cybersecurity product")
        ew_recipient = st.text_input("Who is it to?", placeholder="e.g. Small business owner, 40s, busy, skeptical")
        c1, c2 = st.columns(2)
        with c1: ew_tone = st.selectbox("Tone:", ["Professional","Friendly","Urgent","Casual","Authoritative","Australian Casual"])
        with c2: ew_cta  = st.text_input("Call to Action:", placeholder="e.g. Book a 15-minute call")
        if st.button("✍️ Write Email", use_container_width=True, type="primary"):
            if ew_purpose.strip():
                result, engine = ai_call(
                    f"Write a complete high-converting email:\nPurpose: {ew_purpose}\nRecipient: {ew_recipient}\nTone: {ew_tone}\nCTA: {ew_cta}\n\nInclude: compelling subject line, opening hook, body (problem→solution→proof), clear CTA, sign-off.\nFormat: Subject: [subject] then blank line then body.",
                    system="You are a world-class email copywriter.", max_tokens=550)
                if result: st.text_area("Your email:", value=result, height=260)
                else: st.warning("No AI engine available.")
            else: st.warning("Describe what the email is for.")

    with et4:
        st.markdown("### 📅 Email Drip Sequences")
        st.markdown("""<div class='card card-g'>
<strong>Sequence 1: New Lead (7 Days)</strong><br>
Day 1: Welcome + quick win &nbsp;|&nbsp; Day 2: Educational content (how-to) &nbsp;|&nbsp; Day 3: Case study (social proof)<br>
Day 4: Free trial offer &nbsp;|&nbsp; Day 5: Objection handler (price/value) &nbsp;|&nbsp; Day 6: Scarcity/urgency &nbsp;|&nbsp; Day 7: Final CTA or pivot to nurture
</div>
<div class='card card-p'>
<strong>Sequence 2: Free Trial (7 Days)</strong><br>
Day 1: Welcome + setup guide &nbsp;|&nbsp; Day 2: Feature highlight #1 &nbsp;|&nbsp; Day 3: Check-in (are you stuck?)<br>
Day 4: Feature highlight #2 &nbsp;|&nbsp; Day 5: Case study (results) &nbsp;|&nbsp; Day 6: Upgrade reminder &nbsp;|&nbsp; Day 7: Last chance to convert
</div>""", unsafe_allow_html=True)
        seq_product = st.text_input("Product name:", placeholder="e.g. Email Assassin")
        seq_type    = st.selectbox("Sequence type:", ["New Lead (7 Days)","Free Trial (7 Days)","Post-Purchase (5 Days)","Win-Back (3 Days)","Onboarding (5 Days)"])
        if st.button("🤖 Generate Full Sequence", use_container_width=True):
            if seq_product.strip():
                result, engine = ai_call(
                    f"Write a complete {seq_type} email drip sequence for '{seq_product}'. Write every email in full — subject line and body. Punchy, Australian tone, focused on value and conversion.",
                    system="You are an expert email sequence writer.", max_tokens=2000)
                if result: st.text_area("Your sequence:", value=result, height=400)
                else: st.warning("No AI engine available.")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 — LEAD SCRAPER
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[5]:
    st.markdown("## 🔍 Lead & Email Scraper")
    ls1, ls2, ls3 = st.tabs(["📋 From Text","🌐 From URL","👥 Lead Manager"])

    with ls1:
        raw = st.text_area("Paste any text, webpage content, or directory listing:", height=150)
        if st.button("🔍 Extract Emails", use_container_width=True, type="primary"):
            found = scrape_emails(raw)
            if found:
                st.success(f"Found {len(found)} emails!")
                for e in found: st.markdown(f"- `{e}`")
                if st.button("💾 Save All to Lead List", key="save_text_leads"):
                    added = 0
                    for e in found:
                        if not any(l.get("email") == e for l in leads):
                            leads.append({"email":e,"source":"text","added":now.strftime("%Y-%m-%d"),"status":"New","notes":""})
                            added += 1
                    jsave(LF, leads); st.success(f"Saved {added} new leads!"); st.rerun()
            else: st.info("No emails found in the text.")

    with ls2:
        if not online: st.warning("⚠️ URL scraping requires internet connection.")
        url_in = st.text_input("Website URL:", placeholder="https://example.com/contact")
        bulk   = st.text_area("Or multiple URLs (one per line):", height=80)
        if st.button("🚀 Scrape", use_container_width=True, type="primary"):
            if not online: st.error("No internet connection.")
            else:
                urls = [u.strip() for u in ([url_in] + bulk.split("\n")) if u.strip() and u.startswith("http")]
                all_found = []
                with st.spinner(f"Scraping {len(urls)} URL(s)..."):
                    for url in urls:
                        try:
                            r = requests.get(url, timeout=8, headers={"User-Agent":"Mozilla/5.0"})
                            soup = BeautifulSoup(r.text, "html.parser")
                            for e in scrape_emails(soup.get_text()):
                                all_found.append({"email":e,"source":url})
                        except: pass
                if all_found:
                    st.success(f"Found {len(all_found)} emails!")
                    for item in all_found:
                        st.markdown(f"- `{item['email']}` from `{item['source'][:50]}`")
                    if st.button("💾 Save All"):
                        added = 0
                        for item in all_found:
                            if not any(l.get("email") == item["email"] for l in leads):
                                leads.append({"email":item["email"],"source":item["source"],"added":now.strftime("%Y-%m-%d"),"status":"New","notes":""})
                                added += 1
                        jsave(LF, leads); st.success(f"Saved {added} leads!"); st.rerun()
                else: st.info("No emails found.")

    with ls3:
        st.markdown(f"### 👥 Lead List ({len(leads)} total)")
        col_f, col_clr = st.columns([4, 1])
        with col_clr:
            if st.button("🗑️ Clear All"): jsave(LF, []); st.rerun()
        filter_status = st.selectbox("Filter:", ["All","New","Contacted","Replied","Converted","Dead"])
        filtered = leads if filter_status == "All" else [l for l in leads if l.get("status") == filter_status]
        for i, lead in enumerate(reversed(filtered[-50:])):
            real_idx = leads.index(lead) if lead in leads else -1
            sc = {"New":"#888","Contacted":"#00bfff","Replied":"#ffd700","Converted":"#00ff41","Dead":"#333"}.get(lead.get("status","New"),"#888")
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1: st.markdown(f"`{lead.get('email','')}` <span style='color:#333;font-size:.75em;'>{lead.get('source','')[:30]}</span>", unsafe_allow_html=True)
            with col2: st.markdown(f"<span style='color:{sc};font-size:.8em;'>{lead.get('status','New')}</span>", unsafe_allow_html=True)
            with col3:
                new_status = st.selectbox("", ["New","Contacted","Replied","Converted","Dead"], key=f"ls_{i}", label_visibility="collapsed")
            with col4:
                if st.button("✅", key=f"lsave_{i}") and real_idx >= 0:
                    leads[real_idx]["status"] = new_status; jsave(LF, leads); st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 6 — PRODUCTS
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[6]:
    st.markdown("## 📦 Product Suite — All 15 Products")
    col_summary = st.columns(4)
    col_summary[0].metric("Total MRR", f"${total_mrr:,}")
    col_summary[1].metric("Live Products", sum(1 for p in products if p["status"]=="Live"))
    col_summary[2].metric("Total Customers", total_customers)
    col_summary[3].metric("ARR", f"${total_mrr*12:,}")

    for product in products:
        status_color = {"Live":"#00ff41","Beta":"#ffd700","Ready":"#00bfff","Concept":"#555"}.get(product["status"],"#555")
        with st.expander(f"{product['name']} — [{product['status']}] — ${product['price']}/{'mo' if product['billing']=='month' else 'once'}"):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Price", f"${product['price']}/{'mo' if product['billing']=='month' else 'once'}")
            c2.metric("Customers", product.get("customers", 0))
            c3.metric("MRR", f"${product.get('mrr', 0):,}")
            c4.metric("Status", product["status"])

            if product.get("checklist"):
                st.markdown("**Launch Checklist:**")
                for item, done in list(product["checklist"].items()):
                    new_val = st.checkbox(item, value=done, key=f"chk_{product['name']}_{item}")
                    if new_val != done:
                        product["checklist"][item] = new_val; jsave(PF, products)

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🚀 Set Live", key=f"live_{product['name']}"):
                    for p in products:
                        if p["name"] == product["name"]: p["status"] = "Live"
                    jsave(PF, products); st.success("Live!"); st.rerun()
            with col2:
                nc = st.number_input("Add customers:", 0, 1000, 0, key=f"nc_{product['name']}")
                if st.button("➕ Update Customers", key=f"upd_{product['name']}"):
                    for p in products:
                        if p["name"] == product["name"]:
                            p["customers"] = p.get("customers", 0) + nc
                            if p["billing"] == "month": p["mrr"] = p["customers"] * p["price"]
                    jsave(PF, products); st.success("Updated!"); st.rerun()
            with col3:
                if st.button("🤖 Write Launch Email", key=f"le_{product['name']}"):
                    result, engine = ai_call(f"Write a launch announcement email for '{product['name']}' at ${product['price']}/{'month' if product['billing']=='month' else 'one-time'}. Punchy, exciting, Australian tone. Include subject line.", system="You are an expert product launch copywriter.", max_tokens=400)
                    if result: st.text_area("Launch email:", value=result, height=200, key=f"let_{product['name']}")

    st.markdown("---")
    st.markdown("### ➕ Add New Product")
    with st.form("new_prod"):
        np_name = st.text_input("Name:"); np_price = st.number_input("Price ($):", 1, value=97)
        np_bill = st.selectbox("Billing:", ["month","once"]); np_status = st.selectbox("Status:", ["Ready","Beta","Live","Concept"])
        if st.form_submit_button("Add Product"):
            products.append({"name":np_name,"price":np_price,"billing":np_bill,"status":np_status,"customers":0,"mrr":0,"checklist":{}})
            jsave(PF, products); st.success(f"{np_name} added!"); st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 7 — REVENUE
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[7]:
    st.markdown("## 💰 Revenue Dashboard")
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total MRR", f"${total_mrr:,}")
    k2.metric("ARR", f"${total_mrr*12:,}")
    k3.metric("Customers", total_customers)
    k4.metric("Today", f"${revenue.get('today',0):,}")
    k5.metric("All-Time", f"${sum(e.get('amount',0) for e in revenue.get('history',[]))+revenue.get('today',0):,}")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 💰 Revenue by Product")
        for p in sorted(products, key=lambda x: x.get("mrr",0), reverse=True):
            if p.get("mrr", 0) > 0:
                pct = p["mrr"] / total_mrr if total_mrr > 0 else 0
                st.markdown(f"**{p['name']}:** ${p['mrr']:,}/mo ({pct*100:.0f}%) — {p.get('customers',0)} customers")
                st.progress(pct)

        st.markdown("---")
        st.markdown("### ➕ Log Revenue")
        with st.form("rev_form"):
            ra = st.number_input("Amount ($):", 1, value=100)
            rs = st.text_input("Source:", placeholder="e.g. Email Assassin — new customer")
            if st.form_submit_button("💰 Log It"):
                revenue["today"] = revenue.get("today", 0) + ra
                revenue.setdefault("history", []).append({"amount":ra,"source":rs,"date":now.strftime("%Y-%m-%d"),"time":now.strftime("%H:%M")})
                jsave(RF, revenue)
                send_telegram(f"💰 Revenue logged: +${ra:,}\n{rs}")
                st.success(f"+${ra:,} logged!"); st.rerun()

        st.markdown("### 📋 Revenue History")
        for e in reversed(revenue.get("history", [])[-15:]):
            st.markdown(f"<span style='color:#00ff41;'>+${e['amount']:,}</span> — {e.get('source','')} <span style='color:#222;font-size:.75em;'>{e.get('date','')} {e.get('time','')}</span>", unsafe_allow_html=True)

    with col2:
        st.markdown("### 📈 Growth Projection")
        if CHART_LIB:
            months = ["Now","M3","M6","M9","M12"]
            proj   = [total_mrr, max(total_mrr*2.4,1), max(total_mrr*4.2,1), max(total_mrr*7,1), max(total_mrr*12,1)]
            df = pd.DataFrame({"Month": months, "MRR": proj})
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df["Month"], y=df["MRR"], mode="lines+markers",
                                     line=dict(color="#00ff41", width=3), marker=dict(size=8, color="#ff0080"),
                                     fill="tozeroy", fillcolor="rgba(0,255,65,0.05)"))
            fig.update_layout(paper_bgcolor="#000", plot_bgcolor="#000", font=dict(color="#555"),
                              xaxis=dict(gridcolor="#0a0a0a"), yaxis=dict(gridcolor="#0a0a0a", tickprefix="$"),
                              margin=dict(l=0,r=0,t=10,b=0), height=250)
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("### 🎯 Revenue Milestones")
        for label, target in [("$5K MRR",5000),("$10K MRR",10000),("$25K MRR",25000),("$50K MRR",50000)]:
            pct = min(total_mrr/target, 1.0)
            col = "#00ff41" if pct>=1.0 else "#ffd700" if pct>0.5 else "#ff0080"
            st.markdown(f"<span style='color:{col};font-weight:700;'>{label}</span> {'✅' if pct>=1.0 else f'{pct*100:.0f}%'}", unsafe_allow_html=True)
            st.progress(pct)

        st.markdown("### 💡 Revenue Projections")
        for m, r in [("Month 1","$3K–$5K"),("Month 3","$12K–$15K"),("Month 6","$25K–$30K"),("Month 12","$50K+")]:
            st.markdown(f"<span style='color:#333;'>{m}:</span> <strong style='color:#00ff41;'>{r} MRR</strong>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 8 — PODCAST STUDIO
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[8]:
    st.markdown("## 🎙️ Podcast Studio")
    st.markdown("<p style='color:#555;font-size:.85em;'>Generate full broadcast-ready podcast scripts using your local Llama. Paste into ElevenLabs or any TTS tool to create audio.</p>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        pod_title  = st.text_input("Episode Title:", placeholder="e.g. How AI is Killing the 9-5 for Tradies")
        pod_topic  = st.text_area("Topic / Key Points:", height=90, placeholder="Cover: AI tools for small business, cost savings, real examples, call to action for free trial")
        pod_length = st.selectbox("Length:", ["5 minutes (~700 words)","10 minutes (~1400 words)","20 minutes (~2800 words)"])
        pod_style  = st.selectbox("Style:", ["Solo Host","Interview Format","Storytelling","Educational/How-To","News & Commentary"])
    with col2:
        pod_host   = st.text_input("Host Name:", "Max")
        pod_guest  = st.text_input("Guest Name (interview only):", placeholder="Leave blank for solo")
        pod_cta    = st.text_input("Call to Action:", placeholder="e.g. Visit avatarempire.com for a free trial")
        pod_sponsor= st.text_input("Sponsor (optional):", placeholder="e.g. This episode brought to you by...")

    if st.button("🎙️ Generate Full Podcast Script", use_container_width=True, type="primary"):
        if pod_topic.strip():
            prompt = f"""Write a complete, broadcast-ready podcast script:
Title: {pod_title} | Host: {pod_host} | {"Guest: "+pod_guest if pod_guest else "Format: Solo"} | Style: {pod_style} | Length: {pod_length}
Topic: {pod_topic} | CTA: {pod_cta} | {"Sponsor: "+pod_sponsor if pod_sponsor else ""}

Write the FULL script including:
- Intro music cue and host intro
- Opening hook (first 30 seconds must grab attention)
- Full episode content with natural speech patterns, [PAUSE] markers, [EMPHASIS] markers
- Smooth transitions between segments
- {"Sponsor read (60 seconds)" if pod_sponsor else ""}
- Strong outro with CTA
- Outro music cue

Write it exactly as it would be spoken. Include stage directions in [brackets]."""

            with st.spinner("Writing your podcast script..."):
                result, engine = ai_call(prompt, system=f"You are an expert podcast scriptwriter. Write natural, engaging scripts that sound great when spoken aloud.", max_tokens=2500)

            if result:
                st.success(f"✅ Script generated via {engine}!")
                st.text_area("Your Podcast Script:", value=result, height=450)
                st.download_button("⬇️ Download Script", data=result,
                                   file_name=f"podcast_{pod_title[:30].replace(' ','_')}.txt", mime="text/plain")
                st.markdown("---")
                st.markdown("""<div class='card card-b'>
<strong>🔊 Turn Script into Audio:</strong><br>
<strong>Option 1 — ElevenLabs (Best Quality):</strong> Copy script → elevenlabs.io → choose voice → generate → download MP3<br>
<strong>Option 2 — LM Studio TTS:</strong> If your LM Studio has a TTS model loaded, use it locally for free<br>
<strong>Option 3 — Free:</strong> ttsmaker.com or ttsfree.com — paste script, download MP3
</div>""", unsafe_allow_html=True)
            else: st.warning("No AI engine — start LM Studio or add OpenAI key in Settings.")
        else: st.warning("Enter a topic first.")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 9 — WEB TOOLS
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[9]:
    st.markdown("## 🌐 Web Tools")
    wt1, wt2, wt3 = st.tabs(["🌐 Web Redesigner","📱 Mini App Cloner","🚀 Landing Page Builder"])

    with wt1:
        st.markdown("### 🌐 AI Web Redesigner (Pimly-Style)")
        st.markdown("<p style='color:#555;font-size:.85em;'>Paste any URL — AI analyses the site and rebuilds it as a clean, modern, deployable HTML page. Works on all URLs.</p>", unsafe_allow_html=True)
        wr_url = st.text_input("Website URL:", placeholder="https://anywebsite.com")
        wr_style = st.selectbox("Redesign Style:", ["Modern Dark (like this dashboard)","Clean White Minimal","Bold Corporate","Startup Landing Page","Australian Trade Business","E-commerce"])
        wr_notes = st.text_input("Specific instructions:", placeholder="e.g. Keep the same content but make it look premium, add a contact form")
        if st.button("🎨 Redesign Website", use_container_width=True, type="primary"):
            if wr_url.strip():
                site_content = ""
                if online:
                    try:
                        r = requests.get(wr_url, timeout=10, headers={"User-Agent":"Mozilla/5.0"})
                        soup = BeautifulSoup(r.text, "html.parser")
                        for tag in soup(["script","style","nav","footer","header"]): tag.decompose()
                        site_content = soup.get_text(separator="\n", strip=True)[:3000]
                    except: site_content = ""
                site_section = ("Site content:\n" + site_content) if site_content else "No content available — create a professional redesign based on the URL."
                prompt = f"""Redesign this website as a complete, single-file HTML page.
URL: {wr_url}
Style: {wr_style}
Instructions: {wr_notes}
{site_section}

Output: Complete HTML file with embedded CSS. Modern, responsive, professional. Include all sections from the original. Make it look stunning."""
                with st.spinner("Redesigning..."):
                    result, engine = ai_call(prompt, system="You are an expert web designer. Output complete, production-ready HTML/CSS. No explanations, just the code.", max_tokens=3000)
                if result:
                    html_code = result
                    if "```html" in html_code: html_code = html_code.split("```html")[1].split("```")[0]
                    elif "```" in html_code: html_code = html_code.split("```")[1].split("```")[0]
                    st.success(f"✅ Redesigned via {engine}!")
                    st.download_button("⬇️ Download HTML", data=html_code, file_name="redesigned_site.html", mime="text/html")
                    with st.expander("View HTML Code"): st.code(html_code, language="html")
                    st.components.v1.html(html_code, height=500, scrolling=True)
                else: st.warning("No AI engine available.")
            else: st.warning("Enter a URL first.")

    with wt2:
        st.markdown("### 📱 Mini App Cloner")
        st.markdown("<p style='color:#555;font-size:.85em;'>Paste a URL or describe an app — AI builds a functional single-file HTML version you can use immediately.</p>", unsafe_allow_html=True)
        clone_url = st.text_input("App URL to clone:", placeholder="https://app.example.com")
        clone_desc = st.text_area("Or describe what to build:", height=80, placeholder="e.g. A simple invoice calculator where I enter items and it totals them up with GST")
        clone_type = st.selectbox("App type:", ["Invoice Calculator","Quote Generator","Lead Capture Form","Contact Form","Booking Form","Price Calculator","ROI Calculator","Checklist App","Timer/Tracker","Custom"])
        if st.button("🔨 Build App", use_container_width=True, type="primary"):
            target = clone_url or clone_desc
            if target.strip():
                prompt = f"""Build a complete, functional single-file HTML app:
Target: {target}
Type: {clone_type}
Requirements: Fully functional, no external dependencies, embedded CSS (dark theme), embedded JavaScript, mobile-responsive, professional UI.
Output: Complete HTML file only. No explanations."""
                with st.spinner("Building your app..."):
                    result, engine = ai_call(prompt, system="You are an expert frontend developer. Build complete, functional HTML apps with embedded CSS and JavaScript.", max_tokens=3000)
                if result:
                    html_code = result
                    if "```html" in html_code: html_code = html_code.split("```html")[1].split("```")[0]
                    elif "```" in html_code: html_code = html_code.split("```")[1].split("```")[0]
                    st.success(f"✅ App built via {engine}!")
                    st.download_button("⬇️ Download App", data=html_code, file_name=f"{clone_type.lower().replace(' ','_')}_app.html", mime="text/html")
                    st.components.v1.html(html_code, height=400, scrolling=True)
                else: st.warning("No AI engine available.")
            else: st.warning("Enter a URL or description.")

    with wt3:
        st.markdown("### 🚀 AI Landing Page Builder")
        lp_product = st.text_input("Product/Service name:", placeholder="e.g. Email Assassin", key="lp_product")
        lp_tagline = st.text_input("Tagline:", placeholder="e.g. AI-powered email responses in 10 seconds", key="lp_tagline")
        lp_price   = st.text_input("Price:", placeholder="e.g. $97/month", key="lp_price")
        lp_audience= st.text_input("Target audience:", placeholder="e.g. Small business owners who hate writing emails", key="lp_audience")
        lp_benefits= st.text_area("Key benefits (one per line):", height=90, placeholder="Saves 10 hours per week\nNever miss a lead again\nProfessional replies every time")
        lp_cta     = st.text_input("CTA button text:", "Start Free Trial", key="lp_cta")
        lp_style   = st.selectbox("Style:", ["Dark & Premium","Clean White","Bold & Energetic","Minimal SaaS","Australian Trade"])
        if st.button("🚀 Build Landing Page", use_container_width=True, type="primary"):
            if lp_product.strip():
                prompt = f"""Build a complete, conversion-optimised landing page:
Product: {lp_product} | Tagline: {lp_tagline} | Price: {lp_price} | Audience: {lp_audience}
Benefits: {lp_benefits} | CTA: {lp_cta} | Style: {lp_style}

Include: Hero section, problem/solution, benefits, social proof section, pricing, FAQ, strong CTA footer.
Output: Complete single-file HTML with embedded CSS. No external dependencies. Mobile responsive."""
                with st.spinner("Building landing page..."):
                    result, engine = ai_call(prompt, system="You are an expert conversion copywriter and web designer. Build landing pages that convert.", max_tokens=3000)
                if result:
                    html_code = result
                    if "```html" in html_code: html_code = html_code.split("```html")[1].split("```")[0]
                    elif "```" in html_code: html_code = html_code.split("```")[1].split("```")[0]
                    st.success(f"✅ Landing page built via {engine}!")
                    st.download_button("⬇️ Download Page", data=html_code, file_name=f"{lp_product.lower().replace(' ','_')}_landing.html", mime="text/html")
                    st.components.v1.html(html_code, height=500, scrolling=True)
                else: st.warning("No AI engine available.")
            else: st.warning("Enter a product name.")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 10 — BUSINESS TOOLS
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[10]:
    st.markdown("## 🚀 AI Business Tools")
    bt1,bt2,bt3,bt4,bt5,bt6,bt7,bt8,bt9 = st.tabs([
        "💰 Quick Quote","📄 Proposal","🧾 Invoice","🎯 Ad Copy",
        "📅 Content Calendar","🕵️ Competitor Spy","💡 Sales Script","🏷️ Business Name","👥 Client Tracker"])

    with bt1:
        st.markdown("### 💰 Quick Quote Generator (3-Tier System)")
        st.markdown("<p style='color:#555;font-size:.85em;'>Based on staff count + cameras. Generates professional quote instantly.</p>", unsafe_allow_html=True)
        c1,c2,c3 = st.columns(3)
        with c1: qq_business = st.text_input("Business name:")
        with c2: qq_staff    = st.number_input("Staff count:", 1, 500, 10)
        with c3: qq_cameras  = st.number_input("Camera heads:", 0, 200, 8)
        qq_industry = st.selectbox("Industry:", ["Mining","Insurance Broker","Mortgage Broker","Medical Centre","Tradie/Construction","Retail","Hospitality","NDIS Provider","Other"])
        tier = "Small" if qq_cameras <= 8 else "Medium" if qq_cameras <= 20 else "Large"
        base_prices = {"Small": 14950, "Medium": 24950, "Large": 49950}
        monthly_fees = {"Small": 1000, "Medium": 1500, "Large": 2500}
        base = base_prices[tier]; monthly = monthly_fees[tier]
        st.markdown(f"""<div class='card card-g'>
<strong>Tier: {tier}</strong> | Cameras: {qq_cameras} | Staff: {qq_staff}<br>
<span style='color:#00ff41;font-size:1.3em;font-weight:900;'>${base:,} upfront + ${monthly:,}/month</span><br>
<span style='color:#555;font-size:.8em;'>3-year contract | Free replacement at 3yr 3mo mark | Australian Gov. spec compliance</span>
</div>""", unsafe_allow_html=True)
        if st.button("📄 Generate Full Quote Document", use_container_width=True):
            result, engine = ai_call(
                f"Write a professional quote document for {qq_business or 'the client'} ({qq_industry}, {qq_staff} staff, {qq_cameras} cameras). Tier: {tier}. Upfront: ${base:,}. Monthly: ${monthly:,}. Include: scope of work, what's included, timeline, payment terms, 3yr 3mo free replacement clause, warranty, next steps.",
                system="You are a professional business proposal writer.", max_tokens=700)
            if result: st.text_area("Quote:", value=result, height=300)

    with bt2:
        st.markdown("### 📄 AI Proposal Machine")
        c1,c2 = st.columns(2)
        with c1:
            prop_client  = st.text_input("Client name:")
            prop_problem = st.text_area("Their problem:", height=70, placeholder="e.g. Spending 3 hours/day on email responses, missing leads")
        with c2:
            prop_solution= st.text_input("Your solution:", placeholder="e.g. Email Assassin — AI auto-reply tool", key="prop_solution")
            prop_price   = st.text_input("Investment:", placeholder="e.g. $297/month", key="prop_price")
        prop_extras = st.text_input("Any extras to include:", placeholder="e.g. 30-day money back, free onboarding call, 3 months support", key="prop_extras")
        if st.button("📄 Generate Proposal", use_container_width=True, type="primary"):
            if prop_client.strip():
                result, engine = ai_call(
                    f"Write a complete, professional business proposal for {prop_client}.\nProblem: {prop_problem}\nSolution: {prop_solution}\nInvestment: {prop_price}\nExtras: {prop_extras}\n\nInclude: Executive summary, problem statement, proposed solution, deliverables, timeline, investment breakdown, ROI justification, terms, next steps. Professional Australian business tone.",
                    system="You are an expert business proposal writer.", max_tokens=1200)
                if result:
                    st.text_area("Proposal:", value=result, height=400)
                    st.download_button("⬇️ Download", data=result, file_name=f"proposal_{prop_client}.txt", mime="text/plain")
                else: st.warning("No AI engine available.")

    with bt3:
        st.markdown("### 🧾 Invoice Builder")
        c1,c2 = st.columns(2)
        with c1:
            inv_to      = st.text_input("Invoice to:")
            inv_from    = st.text_input("From:", "Avatar Empire")
            inv_date    = st.text_input("Date:", now.strftime("%d/%m/%Y"))
            inv_due     = st.text_input("Due date:", "14 days")
        with c2:
            inv_num     = st.text_input("Invoice #:", f"INV-{now.strftime('%Y%m%d')}-001")
            inv_abn     = st.text_input("ABN:", placeholder="12 345 678 901")
        inv_items = st.text_area("Line items (one per line: Description | Qty | Price):", height=100,
                                  placeholder="AI Email Assassin — Monthly Subscription | 1 | 297\nOnboarding Call | 1 | 0")
        if st.button("🧾 Generate Invoice", use_container_width=True, type="primary"):
            lines = [l.strip() for l in inv_items.split("\n") if "|" in l]
            items_parsed = []
            subtotal = 0
            for line in lines:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 3:
                    try:
                        qty = float(parts[1]); price = float(parts[2].replace("$","").replace(",",""))
                        items_parsed.append({"desc":parts[0],"qty":qty,"price":price,"total":qty*price})
                        subtotal += qty * price
                    except: pass
            gst = subtotal * 0.1; total = subtotal + gst
            inv_html = f"""<!DOCTYPE html><html><head><style>
body{{font-family:Arial,sans-serif;max-width:800px;margin:40px auto;color:#333;}}
.header{{display:flex;justify-content:space-between;margin-bottom:30px;}}
h1{{color:#000;font-size:2em;}} .label{{color:#888;font-size:.85em;}}
table{{width:100%;border-collapse:collapse;margin:20px 0;}}
th{{background:#000;color:#fff;padding:10px;text-align:left;}}
td{{padding:10px;border-bottom:1px solid #eee;}}
.total-row{{font-weight:bold;background:#f9f9f9;}}
.grand-total{{font-size:1.3em;color:#000;background:#000;color:#fff;}}
</style></head><body>
<div class="header"><div><h1>INVOICE</h1><p class="label">Invoice #: {inv_num}</p><p class="label">Date: {inv_date}</p><p class="label">Due: {inv_due}</p></div>
<div style="text-align:right"><strong>{inv_from}</strong><br>ABN: {inv_abn}</div></div>
<p><strong>Bill To:</strong> {inv_to}</p>
<table><tr><th>Description</th><th>Qty</th><th>Unit Price</th><th>Total</th></tr>
{"".join(f"<tr><td>{i['desc']}</td><td>{i['qty']}</td><td>${i['price']:,.2f}</td><td>${i['total']:,.2f}</td></tr>" for i in items_parsed)}
<tr class="total-row"><td colspan="3">Subtotal</td><td>${subtotal:,.2f}</td></tr>
<tr class="total-row"><td colspan="3">GST (10%)</td><td>${gst:,.2f}</td></tr>
<tr class="grand-total"><td colspan="3"><strong>TOTAL</strong></td><td><strong>${total:,.2f}</strong></td></tr>
</table>
<p style="color:#888;font-size:.85em;">Payment due within {inv_due}. Bank transfer preferred. Thank you for your business.</p>
</body></html>"""
            st.success(f"Invoice total: ${total:,.2f} (inc. GST)")
            st.download_button("⬇️ Download Invoice HTML", data=inv_html, file_name=f"{inv_num}.html", mime="text/html")
            st.components.v1.html(inv_html, height=400, scrolling=True)

    with bt4:
        st.markdown("### 🎯 AI Ad Copy Generator")
        c1,c2 = st.columns(2)
        with c1:
            ad_product  = st.text_input("Product:", placeholder="e.g. Email Assassin", key="ad_product")
            ad_audience = st.text_input("Audience:", placeholder="e.g. Small business owners", key="ad_audience")
            ad_pain     = st.text_input("Pain point:", placeholder="e.g. Spending hours on email", key="ad_pain")
        with c2:
            ad_platform = st.selectbox("Platform:", ["Facebook/Instagram","Google Ads","LinkedIn","TikTok","YouTube Pre-roll","Twitter/X"])
            ad_cta      = st.text_input("CTA:", "Try Free for 7 Days", key="ad_cta")
            ad_budget   = st.selectbox("Ad type:", ["Single Image Ad","Video Script (30s)","Carousel (3 slides)","Story Ad","Search Ad (Google)"])
        if st.button("🎯 Generate Ad Copy", use_container_width=True, type="primary"):
            if ad_product.strip():
                result, engine = ai_call(
                    f"Write {ad_budget} ad copy for {ad_platform}:\nProduct: {ad_product}\nAudience: {ad_audience}\nPain point: {ad_pain}\nCTA: {ad_cta}\n\nWrite multiple variations (3 headlines, 3 body copy options). Include character counts for each. Platform-optimised.",
                    system="You are an expert paid advertising copywriter.", max_tokens=700)
                if result: st.text_area("Ad copy:", value=result, height=300)
                else: st.warning("No AI engine available.")

    with bt5:
        st.markdown("### 📅 30-Day Content Calendar Builder")
        c1,c2 = st.columns(2)
        with c1:
            cc_niche    = st.text_input("Niche:", placeholder="e.g. AI tools for tradies")
            cc_platforms= st.multiselect("Platforms:", ["TikTok","Instagram","YouTube","LinkedIn","Twitter/X","Blog"], default=["TikTok","Instagram"])
        with c2:
            cc_goal     = st.selectbox("Goal:", ["Build audience","Drive sales","Brand awareness","Lead generation","Community building"])
            cc_month    = st.text_input("Month:", now.strftime("%B %Y"))
        if st.button("📅 Build 30-Day Calendar", use_container_width=True, type="primary"):
            if cc_niche.strip():
                result, engine = ai_call(
                    f"Create a complete 30-day content calendar for {cc_month}:\nNiche: {cc_niche}\nPlatforms: {', '.join(cc_platforms)}\nGoal: {cc_goal}\n\nFor each day: Day number, platform, content type, topic/hook, caption idea. Format as a clean table or numbered list. Include mix of educational, entertaining, promotional (80/20 rule).",
                    system="You are an expert social media strategist.", max_tokens=2500)
                if result:
                    st.text_area("Your calendar:", value=result, height=400)
                    st.download_button("⬇️ Download Calendar", data=result, file_name=f"content_calendar_{cc_month.replace(' ','_')}.txt", mime="text/plain")
                else: st.warning("No AI engine available.")

    with bt6:
        st.markdown("### 🕵️ Competitor Spy Tool")
        comp_url  = st.text_input("Competitor URL:", placeholder="https://competitor.com")
        comp_notes= st.text_input("What you know about them:", placeholder="e.g. They charge $500/month, target enterprise")
        if st.button("🕵️ Analyse Competitor", use_container_width=True, type="primary"):
            comp_content = ""
            if online and comp_url.strip():
                try:
                    r = requests.get(comp_url, timeout=8, headers={"User-Agent":"Mozilla/5.0"})
                    soup = BeautifulSoup(r.text, "html.parser")
                    comp_content = soup.get_text(separator=" ", strip=True)[:2500]
                except: pass
            result, engine = ai_call(
                f"Analyse this competitor and give me a strategic breakdown:\nURL: {comp_url}\nAdditional info: {comp_notes}\n{'Content: '+comp_content if comp_content else ''}\n\nProvide:\n1. Their positioning and target market\n2. Pricing strategy\n3. Key strengths\n4. Weaknesses and gaps\n5. How to beat them (3 specific tactics)\n6. Messaging to steal their customers\n7. Pricing recommendation to undercut/outvalue",
                system="You are a ruthless competitive intelligence analyst.", max_tokens=900)
            if result: st.text_area("Competitor analysis:", value=result, height=350)
            else: st.warning("No AI engine available.")

    with bt7:
        st.markdown("### 💡 AI Sales Script Generator")
        c1,c2 = st.columns(2)
        with c1:
            ss_product   = st.text_input("Product:", placeholder="e.g. Email Assassin", key="ss_product")
            ss_price     = st.text_input("Price:", placeholder="e.g. $297/month", key="ss_price")
            ss_audience  = st.text_input("Prospect type:", placeholder="e.g. Busy tradie business owner", key="ss_audience")
        with c2:
            ss_objection = st.selectbox("Main objection:", ["Too expensive","Need to think about it","Not sure I need it","Already have something","No time to implement","Not tech savvy"])
            ss_format    = st.selectbox("Format:", ["Cold Call Script","Discovery Call","Demo Close","Objection Handler","Text/DM Script","Video Sales Letter"])
        if st.button("💡 Generate Script", use_container_width=True, type="primary"):
            if ss_product.strip():
                result, engine = ai_call(
                    f"Write a complete word-for-word {ss_format} for:\nProduct: {ss_product} at {ss_price}\nProspect: {ss_audience}\nMain objection to handle: {ss_objection}\n\nInclude: Opening, rapport building, discovery questions, pitch, objection handling, close, follow-up. Write every word they should say.",
                    system="You are a world-class sales trainer. Write scripts that close deals.", max_tokens=900)
                if result: st.text_area("Sales script:", value=result, height=350)
                else: st.warning("No AI engine available.")

    with bt8:
        st.markdown("### 🏷️ Business Name & Tagline Generator")
        bn_desc    = st.text_area("Describe the business:", height=70, placeholder="e.g. AI tools for Australian tradies — quotes, invoices, scheduling, automated")
        bn_style   = st.selectbox("Name style:", ["Professional & Corporate","Punchy & Memorable","Tech/Modern","Australian","Descriptive","Abstract/Creative"])
        if st.button("🏷️ Generate Names", use_container_width=True, type="primary"):
            if bn_desc.strip():
                result, engine = ai_call(
                    f"Generate 10 business names + taglines for: {bn_desc}\nStyle: {bn_style}\n\nFor each: Name, tagline (under 10 words), domain availability tip, why it works. Make them memorable and brandable.",
                    system="You are a brand naming expert.", max_tokens=700)
                if result: st.text_area("Names & taglines:", value=result, height=350)
                else: st.warning("No AI engine available.")

    with bt9:
        st.markdown("### 👥 Client Follow-Up Tracker")
        with st.form("add_client"):
            c1,c2,c3 = st.columns(3)
            with c1: cl_name = st.text_input("Client name:")
            with c2: cl_email = st.text_input("Email:")
            with c3: cl_followup = st.text_input("Follow-up date:", now.strftime("%Y-%m-%d"))
            cl_notes = st.text_input("Notes:", placeholder="e.g. Interested in Email Assassin, needs demo")
            cl_value = st.number_input("Deal value ($):", 0, value=0)
            if st.form_submit_button("➕ Add Client"):
                clients.append({"name":cl_name,"email":cl_email,"followup":cl_followup,"notes":cl_notes,
                                 "value":cl_value,"status":"Active","added":now.strftime("%Y-%m-%d")})
                jsave(CLIF, clients); st.success(f"{cl_name} added!"); st.rerun()

        st.markdown(f"### 👥 Client List ({len(clients)} clients)")
        overdue = [c for c in clients if c.get("followup","") < now.strftime("%Y-%m-%d") and c.get("status")=="Active"]
        if overdue:
            st.markdown(f'<span class="pill-off">⚠️ {len(overdue)} overdue follow-ups!</span>', unsafe_allow_html=True)
        for i, client in enumerate(reversed(clients[-20:])):
            is_overdue = client.get("followup","") < now.strftime("%Y-%m-%d") and client.get("status")=="Active"
            border = "card-p" if is_overdue else "card-g"
            st.markdown(f"""<div class='card {border}'>
<strong>{client['name']}</strong> {f"<span style='color:#888;font-size:.8em;'>{client['email']}</span>" if client.get('email') else ""}
{f"<span style='color:#ffd700;font-size:.8em;'>💰 ${client['value']:,}</span>" if client.get('value') else ""}
{f"<span style='color:#ff4444;font-size:.8em;'> ⚠️ OVERDUE</span>" if is_overdue else ""}
<br><span style='color:#555;font-size:.8em;'>Follow-up: {client.get('followup','')} | {client.get('notes','')[:60]}</span>
</div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 11 — TASK SHEET
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[11]:
    st.markdown("## 📋 Daily Task Sheet")
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"### {now.strftime('%A %d %B %Y')}")
        cats = ["All"] + sorted(set(t.get("category","General") for t in tasksheet))
        cat_filter = st.selectbox("Category:", cats)
        filtered_tasks = tasksheet if cat_filter == "All" else [t for t in tasksheet if t.get("category") == cat_filter]
        pending = [t for t in filtered_tasks if not t.get("done")]
        done = [t for t in filtered_tasks if t.get("done")]
        st.markdown(f"**{len(pending)} pending · {len(done)} done today**")

        for i, task in enumerate(pending):
            real_idx = tasksheet.index(task) if task in tasksheet else -1
            c1,c2,c3 = st.columns([3,1,1])
            with c1:
                pri_color = {"🔴 High":"#ff4444","🟡 Medium":"#ffd700","🟢 Low":"#00ff41"}.get(task.get("priority","🟢 Low"),"#555")
                st.markdown(f"<span style='color:{pri_color};font-size:.75em;'>{task.get('priority','')}</span> {task.get('task','')}", unsafe_allow_html=True)
            with c2:
                st.markdown(f"<span style='color:#333;font-size:.75em;'>{task.get('category','')}</span>", unsafe_allow_html=True)
            with c3:
                if st.button("✅", key=f"done_{i}") and real_idx >= 0:
                    tasksheet[real_idx]["done"] = True
                    tasksheet[real_idx]["completed"] = now.strftime("%H:%M")
                    jsave(TASKF, tasksheet); st.rerun()

        if done:
            st.markdown(f"---\n**✅ Completed ({len(done)})**")
            for task in done[-5:]:
                st.markdown(f"<span style='color:#1a1a1a;text-decoration:line-through;font-size:.85em;'>✅ {task.get('task','')}</span>", unsafe_allow_html=True)

        st.markdown("---")
        with st.form("add_task_form"):
            c1,c2,c3 = st.columns([3,1,1])
            with c1: new_task = st.text_input("New task:", label_visibility="collapsed", placeholder="Add task...")
            with c2: new_pri  = st.selectbox("", ["🔴 High","🟡 Medium","🟢 Low"], label_visibility="collapsed")
            with c3: new_cat  = st.selectbox("", ["General","Sales","Content","Tech","Admin","Agent","Finance"], label_visibility="collapsed")
            if st.form_submit_button("➕ Add"):
                if new_task.strip():
                    tasksheet.append({"task":new_task,"priority":new_pri,"done":False,"category":new_cat,
                                       "date":now.strftime("%Y-%m-%d"),"added":now.strftime("%H:%M")})
                    jsave(TASKF, tasksheet); st.rerun()

        c1,c2 = st.columns(2)
        with c1:
            if st.button("🤖 AI Plan for Today", use_container_width=True):
                result, engine = ai_call(
                    f"It's {now.strftime('%A')}. AI tools business. MRR ${total_mrr:,}. {len(leads)} leads. {len(pending_tasks)} pending tasks. Give me 8 specific actions for today. Numbered list.",
                    system="You are a sharp business coach.", max_tokens=400)
                if result:
                    lines = [re.sub(r'^\d+[\.\)]\s*','',l.strip()) for l in result.split("\n") if l.strip() and l.strip()[0].isdigit()]
                    for line in lines[:8]:
                        if line: tasksheet.append({"task":line,"priority":"🟡 Medium","done":False,"category":"AI Plan","date":now.strftime("%Y-%m-%d"),"added":now.strftime("%H:%M")})
                    jsave(TASKF, tasksheet); st.rerun()
        with c2:
            if st.button("🗑️ Clear Done", use_container_width=True):
                tasksheet = [t for t in tasksheet if not t.get("done")]; jsave(TASKF, tasksheet); st.rerun()

    with col2:
        st.markdown("### 📊 Task Stats")
        total_t = len(tasksheet); done_t = len([t for t in tasksheet if t.get("done")])
        st.metric("Total Tasks", total_t); st.metric("Done", done_t); st.metric("Pending", total_t - done_t)
        if total_t > 0: st.progress(done_t / total_t)

        st.markdown("### 🎯 Today's Focus")
        high_pri = [t for t in tasksheet if t.get("priority") == "🔴 High" and not t.get("done")]
        if high_pri:
            for t in high_pri[:3]:
                st.markdown(f"<span style='color:#ff4444;font-size:.85em;'>🔴 {t['task'][:40]}</span>", unsafe_allow_html=True)
        else: st.markdown("<span style='color:#1a1a1a;font-size:.85em;'>No high priority tasks.</span>", unsafe_allow_html=True)

        st.markdown("### 📋 Revenue Targets")
        st.markdown(f"<span style='color:#555;font-size:.85em;'>Today's target:</span> <strong style='color:#00ff41;'>$500+</strong>", unsafe_allow_html=True)
        st.markdown(f"<span style='color:#555;font-size:.85em;'>This week:</span> <strong style='color:#00ff41;'>$2,000+</strong>", unsafe_allow_html=True)
        st.markdown(f"<span style='color:#555;font-size:.85em;'>This month:</span> <strong style='color:#00ff41;'>${max(total_mrr, 3000):,}+</strong>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 12 — SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[12]:
    st.markdown("## ⚙️ Settings")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🤖 AI Engine")
        st.markdown('<span class="pill-ai">LM Studio → Ollama → OpenAI (auto-fallback)</span>', unsafe_allow_html=True)
        lm_url   = st.text_input("LM Studio URL:", S.get("lm_studio_url","http://localhost:1234/v1"))
        lm_model = st.text_input("LM Studio Model:", S.get("lm_model","Llama-3.2-1B-Instruct-Q5_K_M"))
        ol_url   = st.text_input("Ollama URL:", S.get("ollama_url","http://localhost:11434/v1"))
        ol_model = st.text_input("Ollama Model:", S.get("ollama_model","llama3.2:1b"))
        oai_key  = st.text_input("OpenAI API Key (fallback):", S.get("openai_key",""), type="password")

        st.markdown("### 🌤️ Weather")
        w_city = st.text_input("City:", S.get("weather_city","Sydney"))
        w_key  = st.text_input("OpenWeatherMap API Key (free):", S.get("weather_key",""), type="password",
                                help="Free at openweathermap.org/api — takes 2 minutes")

    with col2:
        st.markdown("### 📱 Telegram Notifications")
        st.markdown("""<div class='card card-b'>
<strong>Setup (2 minutes):</strong><br>
1. Open Telegram → search @BotFather<br>
2. Send /newbot → follow steps → copy token<br>
3. Search @userinfobot → send /start → copy your Chat ID<br>
4. Paste both below and save
</div>""", unsafe_allow_html=True)
        tg_token   = st.text_input("Telegram Bot Token:", S.get("telegram_token",""), type="password")
        tg_chat_id = st.text_input("Telegram Chat ID:", S.get("telegram_chat_id",""))
        if st.button("🔔 Test Telegram"):
            S_test = dict(S); S_test["telegram_token"] = tg_token; S_test["telegram_chat_id"] = tg_chat_id
            jsave(SF, S_test)
            sent = send_telegram(f"🎭 Avatar Empire test notification!\nMRR: ${total_mrr:,} | {now.strftime('%d %b %Y %H:%M')}")
            st.success("Sent! Check Telegram." if sent else "Failed — check token and chat ID.")

        st.markdown("### 🌐 Online Deployment")
        st.markdown("""<div class='card card-g'>
<strong>Deploy to Streamlit Cloud (free):</strong><br>
1. Push code to GitHub<br>
2. Go to share.streamlit.io<br>
3. Connect repo → deploy<br>
4. Access from any device, anywhere<br><br>
<strong>Run locally (offline):</strong><br>
<code>streamlit run app.py</code><br>
Works 100% offline with LM Studio running
</div>""", unsafe_allow_html=True)

    if st.button("💾 Save All Settings", use_container_width=True, type="primary"):
        new_settings = {
            "openai_key": oai_key, "lm_studio_url": lm_url, "lm_model": lm_model,
            "ollama_url": ol_url, "ollama_model": ol_model,
            "telegram_token": tg_token, "telegram_chat_id": tg_chat_id,
            "weather_city": w_city, "weather_key": w_key
        }
        jsave(SF, new_settings)
        st.success("✅ Settings saved! Refresh to apply.")
        send_telegram(f"⚙️ Settings updated on Avatar Empire\n{now.strftime('%d %b %Y %H:%M')}")

    st.markdown("---")
    st.markdown("### 📊 System Status")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Internet", "🟢 Online" if online else "🔴 Offline")
    c2.metric("Products", len(products))
    c3.metric("Leads", len(leads))
    c4.metric("Avatars", len(avatars))
    st.markdown(f"<span style='color:#1a1a1a;font-size:.75em;'>Data stored locally in /data/ · All settings encrypted in JSON · v3.0 · {now.strftime('%Y')}</span>", unsafe_allow_html=True)
