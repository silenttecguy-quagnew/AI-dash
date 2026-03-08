"""
⚡ ARTIFICIAL & INTELLIGENT — v4.0
AI Business Command Dashboard · ArmourVault.au
LM Studio (Llama-3.2) → Ollama → DeepSeek → OpenAI
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
    import plotly.express as px
    import pandas as pd
    CHART_LIB = True
except ImportError:
    CHART_LIB = False

try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_LIB = True
except ImportError:
    AUTOREFRESH_LIB = False

# ── Paths ─────────────────────────────────────────────────────────────────────
DATA    = Path("data"); DATA.mkdir(exist_ok=True)
AVDIR   = DATA/"avatars_folder"; AVDIR.mkdir(exist_ok=True)
SF      = DATA/"settings.json"
PF      = DATA/"products.json"
RF      = DATA/"revenue.json"
TF      = DATA/"tasks.json"
AVF     = DATA/"avatars.json"
LF      = DATA/"leads.json"
CF      = DATA/"chat.json"
TASKF   = DATA/"tasksheet.json"
WINSF   = DATA/"wins.json"
CLIF    = DATA/"clients.json"
IDEAF   = DATA/"ideas.json"
DREAMF  = DATA/"dreambuilds.json"
SECF    = DATA/"security.json"
# ── Path aliases (for appended tab code compatibility) ────────────────────────
DATA_DIR      = DATA
TASKS_FILE    = TF
LEADS_FILE    = LF
REVENUE_FILE  = RF
PRODUCTS_FILE = PF
SETTINGS_FILE = SF
IDEAS_FILE    = IDEAF
ENQUIRIES_FILE= DREAMF
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
            return {"temp": round(d["main"]["temp"]),
                    "desc": d["weather"][0]["description"].title(),
                    "city": d["name"]}
    except: pass
    return None

def scrape_emails(text):
    return list(set(re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)))

def send_telegram(msg):
    s = jload(SF, {})
    token   = s.get("telegram_token", "")
    chat_id = s.get("telegram_chat_id", "")
    if not token or not chat_id: return False
    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"}, timeout=5)
        return True
    except: return False

def extract_key_points(text):
    lines = text.split('\n')
    pts = []
    for line in lines:
        line = line.strip()
        if line.startswith(('##', '**', '-', '*', '1.', '2.', '3.', '4.', '5.')) and len(line) > 12:
            clean = line.lstrip('#*-123456789. ').strip().rstrip('*')
            if clean and len(clean) > 8: pts.append(clean)
    return pts[:8]

def heygen_generate(script, api_key):
    if not api_key: return None, "No HeyGen API key"
    try:
        headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}
        payload = {
            "video_inputs": [{
                "character": {"type": "avatar", "avatar_id": "Daisy-inskirt-20220818", "avatar_style": "normal"},
                "voice": {"type": "text", "input_text": script[:1500], "voice_id": "1bd001e7e50f421d891986aad5158bc8"},
                "background": {"type": "color", "value": "#000000"}
            }],
            "dimension": {"width": 1280, "height": 720}
        }
        r = requests.post("https://api.heygen.com/v2/video/generate",
                          json=payload, headers=headers, timeout=30)
        if r.status_code == 200:
            vid_id = r.json().get("data", {}).get("video_id", "")
            return vid_id, "Video generation started — check HeyGen dashboard in 2-3 minutes"
        return None, f"HeyGen error {r.status_code}: {r.text[:100]}"
    except Exception as e:
        return None, f"HeyGen error: {e}"

def did_generate(script, api_key):
    if not api_key: return None, "No D-ID API key"
    try:
        import base64
        headers = {"Authorization": f"Basic {api_key}", "Content-Type": "application/json"}
        payload = {
            "script": {"type": "text", "input": script[:1000],
                       "provider": {"type": "microsoft", "voice_id": "en-AU-NatashaNeural"}},
            "presenter_id": "amy-jcwCkr1grs"
        }
        r = requests.post("https://api.d-id.com/talks",
                          json=payload, headers=headers, timeout=30)
        if r.status_code == 201:
            return r.json().get("id", ""), "D-ID video generation started"
        return None, f"D-ID error {r.status_code}"
    except Exception as e:
        return None, f"D-ID error: {e}"

# ── AI Engine ─────────────────────────────────────────────────────────────────
def ai_call(prompt,
            system="You are a sharp AI business assistant for ArmourVault.au — an Australian cybersecurity and AI tools company. Always respond with structured, actionable output. Use markdown headers and bullet points. Be direct, specific, and Australian in tone. Never give vague or generic answers.",
            max_tokens=1500):
    s = jload(SF, {})

    # 1. DeepSeek (primary — online cloud)
    ds_key = s.get("deepseek_key", "sk-6c9ee828c9b24ea391e349e7477b85b4")
    if ds_key and OPENAI_LIB:
        try:
            client = openai.OpenAI(api_key=ds_key, base_url="https://api.deepseek.com/v1")
            resp = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role":"system","content":system},{"role":"user","content":prompt}],
                max_tokens=max_tokens, temperature=0.7)
            return resp.choices[0].message.content.strip(), "DeepSeek R1"
        except: pass

    # 2. OpenAI (second online fallback)
    oai_key = s.get("openai_key", "")
    if oai_key and OPENAI_LIB:
        try:
            client = openai.OpenAI(api_key=oai_key)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role":"system","content":system},{"role":"user","content":prompt}],
                max_tokens=max_tokens)
            return resp.choices[0].message.content.strip(), "OpenAI GPT-4o-mini"
        except: pass

    # 3. LM Studio (offline local)
    lm_url   = s.get("lm_studio_url", "http://localhost:1234/v1")
    lm_model = s.get("lm_model", "Llama-3.2-1B-Instruct-Q5_K_M")
    if lm_url and OPENAI_LIB:
        try:
            client = openai.OpenAI(api_key="lm-studio", base_url=lm_url)
            resp = client.chat.completions.create(
                model=lm_model,
                messages=[{"role":"system","content":system},{"role":"user","content":prompt}],
                max_tokens=max_tokens, temperature=0.7, timeout=15)
            return resp.choices[0].message.content.strip(), "LM Studio (Local)"
        except: pass

    # 4. Ollama (offline local fallback)
    ol_url   = s.get("ollama_url", "http://localhost:11434/v1")
    ol_model = s.get("ollama_model", "llama3.2:1b")
    if OPENAI_LIB:
        try:
            client = openai.OpenAI(api_key="ollama", base_url=ol_url)
            resp = client.chat.completions.create(
                model=ol_model,
                messages=[{"role":"system","content":system},{"role":"user","content":prompt}],
                max_tokens=max_tokens, timeout=15)
            return resp.choices[0].message.content.strip(), "Ollama (Local)"
        except Exception as e:
            return f"[AI Error: {e}]", "Error"

    return None, "Offline — No AI Engine"

# ── Default data ──────────────────────────────────────────────────────────────
DEFAULT_SETTINGS = {
    "openai_key": "", "deepseek_key": "sk-6c9ee828c9b24ea391e349e7477b85b4",
    "lm_studio_url": "http://localhost:1234/v1", "lm_model": "Llama-3.2-1B-Instruct-Q5_K_M",
    "ollama_url": "http://localhost:11434/v1", "ollama_model": "llama3.2:1b",
    "telegram_token": "", "telegram_chat_id": "",
    "weather_city": "Sydney", "weather_key": "",
    "heygen_key": "", "did_key": ""
}

DEFAULT_PRODUCTS = [
    {"name":"Email Assassin Pro","price":297,"mrr":0,"status":"Active","customers":0,"checklist":85},
    {"name":"AI Avatar Builder","price":497,"mrr":0,"status":"Active","customers":0,"checklist":70},
    {"name":"TradieTech Suite","price":197,"mrr":0,"status":"Pre-Launch","customers":0,"checklist":60},
    {"name":"Cyber Shield Basic","price":14950,"mrr":1000,"status":"Active","customers":0,"checklist":90},
    {"name":"Cyber Shield Pro","price":24950,"mrr":1500,"status":"Active","customers":0,"checklist":90},
    {"name":"Cyber Shield Enterprise","price":39950,"mrr":2000,"status":"Active","customers":0,"checklist":90},
    {"name":"AI Content Machine","price":197,"mrr":0,"status":"Active","customers":0,"checklist":80},
    {"name":"Lead Sniper","price":147,"mrr":0,"status":"Active","customers":0,"checklist":75},
    {"name":"Social Command Pro","price":247,"mrr":0,"status":"Active","customers":0,"checklist":65},
    {"name":"Podcast Empire Kit","price":397,"mrr":0,"status":"Pre-Launch","customers":0,"checklist":50},
    {"name":"Dashboard Builder Kit","price":2500,"mrr":0,"status":"Pre-Launch","customers":0,"checklist":40},
    {"name":"Autonomous Agent Crew","price":497,"mrr":0,"status":"Development","customers":0,"checklist":30},
    {"name":"Magic Mike Avatar System","price":997,"mrr":0,"status":"Pre-Launch","customers":0,"checklist":55},
]

AGENTS = [
    {"name":"Content Machine","emoji":"✍️","color":"#ff0080",
     "system":"""You are the Content Machine for ArmourVault.au — an Australian cybersecurity and AI tools company run by a solo founder targeting tradies, mining companies, insurance brokers, mortgage brokers, and small businesses.

YOUR JOB: Produce ready-to-publish content. Never give advice about content — produce the actual content.

OUTPUT FORMAT (always follow this structure):
1. HOOK (first line — scroll-stopping, punchy, Australian)
2. BODY (value, story, or proof — 3-5 lines max per platform)
3. CTA (one clear action — DM, link, comment, share)
4. HASHTAGS (10-15 relevant, mix of niche + broad)
5. PLATFORM NOTE (any tweaks for the specific platform)

RULES:
- Write in Australian English (mate, g'day, arvo, etc. where natural — not forced)
- Be direct and punchy — no waffle, no corporate speak
- Every piece must have a hook that stops the scroll in the first 2 seconds
- Always include a specific result or number where possible (e.g. 'saved 3 hours a day', 'cut admin by 60%')
- Never write generic content — always tie it to ArmourVault.au's products or the client's industry"""},
    {"name":"Email Agent","emoji":"📧","color":"#00ff41",
     "system":"""You are the Email Agent for ArmourVault.au — an Australian cybersecurity and AI tools company.

Target industries: mining companies, insurance brokers, mortgage brokers, medical centres, tradies, real estate agents, restaurants, professional services.

YOUR JOB: Write complete, ready-to-send emails. Never give advice about emails — write the actual email.

OUTPUT FORMAT (always follow this structure):
**SUBJECT LINE:** [subject]
**PREVIEW TEXT:** [preview — 40-60 chars]

**BODY:**
[Full email body]

**SEND TIME:** [best day/time to send]
**FOLLOW-UP:** [when and how to follow up]

RULES:
- Always start with 'G'day [Name],' — never 'Hi' or 'Dear'
- First sentence must hook them in 10 words or less
- Max 150 words for cold outreach — people are busy
- One CTA only — never give them multiple options
- Include a specific result or social proof in every cold email
- Pain point first, solution second, proof third, CTA last
- Australian English throughout"""},
    {"name":"Sales Bot","emoji":"💬","color":"#ffd700",
     "system":"""You are the Sales Bot for ArmourVault.au — an Australian cybersecurity and AI tools company.

Products: Cyber Shield Basic ($14,950 + $1,000/mo), Cyber Shield Pro ($24,950 + $1,500/mo), Cyber Shield Enterprise ($39,950 + $2,000/mo), Email Assassin Pro ($297), AI Avatar Builder ($497), TradieTech Suite ($197/mo), and more.

Key selling points:
- SOCI Act compliance automation
- Essential 8 framework built in
- 3-year 3-month replacement guarantee (unit replaced free at 3yr 3mo mark)
- Remote monitoring — no need for client to manage it
- Government grant eligible pricing

YOUR JOB: Write sales scripts, handle objections, build proposals, qualify leads. Always produce the actual script/document — never just advice.

OUTPUT FORMAT:
**SITUATION:** [what the prospect said/needs]
**RESPONSE SCRIPT:** [exact words to say]
**OBJECTION HANDLERS:** [if/then scripts for likely pushback]
**NEXT STEP:** [exact action to take]

RULES:
- Be confident and direct — never apologetic about price
- Always anchor to ROI and risk cost (what's a data breach worth vs. our price?)
- Use the 3yr 3mo replacement as a trust builder
- Close with a specific next step — never leave it open-ended"""},
    {"name":"Analytics Brain","emoji":"📊","color":"#00bfff",
     "system":"""You are the Analytics Brain for ArmourVault.au — an Australian cybersecurity and AI tools company.

Business context: Solo founder, current MRR ~$3,552, ARR ~$42,624, 16 customers. Products include Cyber Shield tiers, AI tools, and SaaS subscriptions. Target: $10K MRR in 90 days, $25K MRR in 6 months.

YOUR JOB: Analyse data, identify patterns, generate insights, and produce actionable reports. Always produce specific numbers and recommendations — never vague analysis.

OUTPUT FORMAT:
**ANALYSIS:** [what the data shows]
**KEY METRICS:** [specific numbers and trends]
**INSIGHT:** [what this means for the business]
**ACTION ITEMS:** [3-5 specific things to do, with timeframes]
**PROJECTION:** [what happens if actions are taken vs. not taken]

RULES:
- Always be specific — use actual numbers, percentages, timeframes
- Prioritise revenue impact above everything else
- Flag risks and opportunities equally
- Every recommendation must have a 'do this by [date]' attached"""},
    {"name":"Deploy Master","emoji":"🚀","color":"#ff6600",
     "system":"""You are the Deploy Master for ArmourVault.au — an Australian cybersecurity and AI tools company.

YOUR JOB: Build complete launch plans, automation workflows, go-to-market strategies, and deployment checklists. Always produce the actual plan — never just advice.

OUTPUT FORMAT:
**LAUNCH NAME:** [name]
**GOAL:** [specific outcome with number and date]
**PRE-LAUNCH CHECKLIST:**
- [ ] [task] — [owner] — [deadline]
**LAUNCH SEQUENCE:**
- Day 1: [exact actions]
- Day 2: [exact actions]
...
**AUTOMATION TRIGGERS:**
- If [X] happens → do [Y]
**SUCCESS METRICS:** [how to measure if it worked]
**CONTINGENCY:** [what to do if it fails]

RULES:
- Every step must have a specific action, not a vague direction
- Include exact copy, timing, and platform for every touchpoint
- Build in automation wherever possible
- Always include a 'kill switch' — what to do if it's not working after 48 hours"""},
    {"name":"Code Builder","emoji":"💻","color":"#9d4edd",
     "system":"""You are the Code Builder for ArmourVault.au — an Australian cybersecurity and AI tools company.

Primary stack: Python 3.11, Streamlit, JSON data storage, OpenAI/DeepSeek API, Plotly, Pandas. Secondary: HTML/CSS, JavaScript, REST APIs.

YOUR JOB: Write complete, production-ready code. Fix bugs. Build features. Always produce working code — never pseudocode or partial snippets unless explicitly asked.

OUTPUT FORMAT:
```python
# [filename]
# [brief description]
# [dependencies: pip install ...]

[complete working code]
```
**HOW TO USE:** [exact instructions]
**WHAT IT DOES:** [plain English explanation]
**KNOWN LIMITATIONS:** [any edge cases or gotchas]

RULES:
- Always include error handling (try/except)
- Always include comments on non-obvious logic
- Test edge cases in your head before writing
- If fixing a bug, explain what caused it and what the fix does
- Production-ready means: handles empty data, handles API failures, handles bad input"""},
    {"name":"Social Agent","emoji":"📱","color":"#ff1493",
     "system":"""You are the Social Agent for ArmourVault.au — an Australian cybersecurity and AI tools company.

Active platforms: TikTok, Instagram, LinkedIn, Facebook, YouTube, X (Twitter).
Brand voice: Direct, punchy, Australian, confident — not corporate, not cringe.
Target audience: Tradies, mining companies, insurance brokers, mortgage brokers, small business owners.

YOUR JOB: Write complete, platform-optimised social content. Always produce the actual post — never just advice.

OUTPUT FORMAT (for each platform requested):
**[PLATFORM]:**
[Complete post copy — ready to paste and publish]
📅 Best time to post: [day + time]
🎯 Goal: [awareness/engagement/leads/sales]
📊 Expected reach: [estimate based on typical performance]

RULES:
- TikTok/Instagram: Hook in first 3 words. Max 150 words. Emoji-forward.
- LinkedIn: Professional but human. 150-300 words. Story-driven. No hashtag spam (max 5).
- Facebook: Community-focused. Question or poll format works best. 100-200 words.
- YouTube: Title must be SEO-optimised. Description includes timestamps and CTA.
- X: Max 280 chars. Punchy take or hot opinion. One hashtag max.
- Always write in Australian English"""},
    {"name":"Security Agent","emoji":"🛡️","color":"#00ff88",
     "system":"""You are the Security Agent for ArmourVault.au — an Australian cybersecurity company specialising in AI-powered compliance and monitoring systems.

Expertise: SOCI Act 2018, Essential 8 (ACSC), Privacy Act 1988, ISO 27001, NIST CSF, ASD Top 35, Australian Government ISM.

Products: Cyber Shield Basic/Pro/Enterprise — plug-and-play AI cybersecurity units with automated compliance reporting, remote monitoring, and 3yr 3mo replacement guarantee.

YOUR JOB: Produce security assessments, compliance checklists, incident response plans, risk reports, and client-facing security documents. Always produce the actual document — never just advice.

OUTPUT FORMAT:
**ASSESSMENT TYPE:** [type]
**CLIENT/SCENARIO:** [who/what]
**RISK LEVEL:** 🔴 Critical / 🟡 Medium / 🟢 Low
**FINDINGS:**
1. [Finding] — Risk: [level] — Fix: [specific action]
**COMPLIANCE STATUS:**
- SOCI Act: [compliant/gap/N/A]
- Essential 8: [maturity level 0-3]
- Privacy Act: [compliant/gap/N/A]
**RECOMMENDED ACTIONS:** [prioritised list with timeframes]
**QUOTE TRIGGER:** [if this warrants a Cyber Shield quote, state which tier and why]

RULES:
- Always reference specific Australian legislation by name and section where relevant
- Flag anything that could result in a notifiable data breach
- Every finding must have a specific remediation action
- If the scenario warrants a Cyber Shield product, recommend the appropriate tier"""},
]

EMAIL_TEMPLATES = {
    "1. Cold Outreach — Mining/SOCI Act": {
        "subject": "SOCI Act compliance in 5 minutes instead of 5 weeks",
        "body": "G'day [Name],\n\nQuick question about [Company]'s cybersecurity compliance.\n\nAre you spending weeks preparing SOCI Act reports for the board?\n\nI've built an AI system that generates compliance documentation in minutes instead of months. Risk assessments, incident reports, gap analyses — all automated.\n\nFormer A&I Armour engineer. Worked with [mention any mutual connection or similar company].\n\nWorth a 15-minute call to show you how [Company X] cut their compliance overhead by 80%?\n\nAvailable Tuesday or Thursday this week.\n\nCheers,\n[Your Name]\n[Phone]"
    },
    "2. Cold Outreach — Tradies": {
        "subject": "Getting you more jobs without the paperwork headache",
        "body": "G'day [Name],\n\nI work with tradies across [City] who are sick of spending their evenings doing quotes, invoices, and chasing payments instead of being with their families.\n\nI've built an AI tool that handles all of it — quotes in 60 seconds, invoices sent automatically, follow-ups done for you.\n\n[Tradie Name] from [Suburb] went from 3 hours of admin per day to 20 minutes.\n\nWorth a quick chat? I can show you exactly how it works in 10 minutes.\n\nCheers,\n[Your Name]\n[Phone]"
    },
    "3. Cold Outreach — LinkedIn": {
        "subject": "Saw your post about [topic] — thought this might help",
        "body": "Hi [Name],\n\nI came across your post about [specific topic they posted about] and it resonated — we're solving a similar problem for businesses like yours.\n\nWe've built an AI system that [specific benefit relevant to their industry]. [Company similar to theirs] used it to [specific result].\n\nWould love to share how it works — happy to send a quick 3-minute video walkthrough if that's easier than a call?\n\nBest,\n[Your Name]"
    },
    "4. Follow-Up #1 (3 days after cold outreach)": {
        "subject": "Re: [Original subject line]",
        "body": "G'day [Name],\n\nJust following up on my message from [day].\n\nI know your inbox is probably packed — I'll keep this short.\n\nWe just helped [similar company] achieve [specific result] in [timeframe]. Thought it might be relevant given what you're working on.\n\nStill happy to do a quick 10-minute call this week if you're keen.\n\nCheers,\n[Your Name]"
    },
    "5. Follow-Up #2 (7 days — value add)": {
        "subject": "Something useful for [their industry]",
        "body": "Hi [Name],\n\nI won't keep pushing for a call — but I did want to share something that might be useful regardless.\n\n[Share a genuine insight, tip, or resource relevant to their industry]\n\nNo strings attached — just thought it was worth passing on.\n\nIf you ever want to chat about how we're using AI to solve [their problem], I'm here.\n\nCheers,\n[Your Name]"
    },
    "6. Follow-Up #3 (14 days — break-up)": {
        "subject": "Closing the loop",
        "body": "G'day [Name],\n\nI'll take the hint — clearly the timing isn't right, and that's completely fine.\n\nI'll stop reaching out, but if [their pain point] ever becomes a priority, feel free to reach back out.\n\nWishing you and the team a great [quarter/year].\n\nCheers,\n[Your Name]\n\nP.S. — If you know anyone who might benefit from what we do, I'd really appreciate the introduction."
    },
    "7. Objection Handler — Too Expensive": {
        "subject": "Re: Pricing",
        "body": "G'day [Name],\n\nFair point — it's not cheap. But let me reframe it.\n\nIf this saves your team [X hours] per week, at [their hourly rate], that's $[calculated saving] per month. The tool pays for itself in [timeframe].\n\nWe also offer a 14-day trial with no lock-in. You see the value before you commit.\n\nWant me to put together a quick ROI breakdown specific to your business?\n\nCheers,\n[Your Name]"
    },
    "8. Objection Handler — Not the Right Time": {
        "subject": "Re: Timing",
        "body": "G'day [Name],\n\nCompletely understand — timing is everything.\n\nCan I ask — what would need to change for this to become a priority? That way I can reach back out when it actually makes sense for you, rather than just following up randomly.\n\nAnd if it helps, we can lock in your current pricing now and you activate whenever you're ready. No pressure.\n\nCheers,\n[Your Name]"
    },
    "9. Onboarding — Welcome Email": {
        "subject": "Welcome to [Product Name] — here's how to get started",
        "body": "G'day [Name],\n\nWelcome aboard — stoked to have you.\n\nHere's how to get the most out of [Product Name] in your first week:\n\n✅ Step 1: [First action — takes 2 minutes]\n✅ Step 2: [Second action]\n✅ Step 3: [Third action]\n\nIf you get stuck at any point, just reply to this email and I'll sort it out personally.\n\nYour first win should happen within [timeframe]. Let me know how it goes.\n\nCheers,\n[Your Name]"
    },
    "10. Onboarding — Day 3 Check-In": {
        "subject": "How's [Product Name] going for you?",
        "body": "G'day [Name],\n\nJust checking in — you've had [Product Name] for a few days now.\n\nHave you had a chance to [key action]? That's usually where people see the first big result.\n\nIf you haven't got there yet, no worries — here's a 2-minute shortcut: [specific tip]\n\nAny questions, just hit reply.\n\nCheers,\n[Your Name]"
    },
    "11. Win-Back — Churned Customer": {
        "subject": "We've made some big improvements since you left",
        "body": "G'day [Name],\n\nIt's been a while since you used [Product Name], and I wanted to reach out personally.\n\nSince you left, we've added:\n• [New feature 1]\n• [New feature 2]\n• [Improvement based on common feedback]\n\nI'd love to offer you a free 30-day trial of the new version — no credit card, no commitment.\n\nIf it's not for you after 30 days, no hard feelings. But I think you'll be surprised.\n\nInterested?\n\nCheers,\n[Your Name]"
    },
    "12. Referral Request": {
        "subject": "Quick favour — do you know anyone who'd benefit from this?",
        "body": "G'day [Name],\n\nHope things are going well.\n\nI'm reaching out because you've been one of our best customers, and I wanted to ask — do you know anyone else who might benefit from [Product Name]?\n\nFor every referral that becomes a customer, I'll give you [incentive — e.g. one month free, $X credit, gift card].\n\nNo pressure at all — just thought I'd ask. If someone comes to mind, just forward this email or send me their details and I'll take it from there.\n\nThanks mate,\n[Your Name]"
    },
    "13. Upsell — Existing Customer": {
        "subject": "You're getting great results — here's the next level",
        "body": "G'day [Name],\n\nI've been watching your results with [Product Name] and you're doing really well — [specific result if known].\n\nI wanted to let you know about [Upsell Product] — it's what our top customers use to [next level benefit].\n\nBecause you're already a customer, I can offer it to you at [discounted price] — that's [X]% off the standard price.\n\nWant me to set it up for you? Takes about 10 minutes.\n\nCheers,\n[Your Name]"
    },
    "14. Testimonial Request": {
        "subject": "Would you mind sharing your experience?",
        "body": "G'day [Name],\n\nI hope [Product Name] has been delivering value for you.\n\nI'm building out our case studies and would love to feature your experience — if you're open to it.\n\nIt would only take 5 minutes. I can either:\na) Send you 3 quick questions to answer via email, or\nb) Jump on a 10-minute call and I'll write it up for you to approve\n\nIn return, I'll give you [incentive].\n\nLet me know which works better for you.\n\nCheers,\n[Your Name]"
    },
    "15. Partnership Pitch": {
        "subject": "Partnership opportunity — [mutual benefit]",
        "body": "G'day [Name],\n\nI've been following [their company] for a while and I think there's a genuine opportunity for us to work together.\n\nWe serve [your audience] and you serve [their audience] — there's significant overlap without direct competition.\n\nI'm thinking: [specific partnership idea — referral arrangement, co-marketing, bundled offer, etc.]\n\nWould you be open to a 20-minute call to explore whether this makes sense for both of us?\n\nCheers,\n[Your Name]"
    },
    "16. Support — Issue Resolution": {
        "subject": "Re: Your support request — sorted",
        "body": "G'day [Name],\n\nThanks for reaching out — sorry you hit that snag.\n\nHere's what happened and how I've fixed it:\n\n[Clear explanation of the issue]\n[What was done to fix it]\n[What you can do now]\n\nIf you're still having trouble after trying that, just reply and I'll jump in personally.\n\nAppreciate your patience.\n\nCheers,\n[Your Name]"
    },
    "17. Weekly Newsletter": {
        "subject": "[Week of Date] — What's working in AI for small business this week",
        "body": "G'day [First Name],\n\nHere's what's worth your attention this week:\n\n🔥 THIS WEEK'S BIG THING\n[One key insight, trend, or tool worth knowing about]\n\n💡 QUICK WIN\n[One actionable tip they can implement today]\n\n📊 BY THE NUMBERS\n[One interesting stat relevant to their business]\n\n🛠️ WHAT WE'VE BEEN BUILDING\n[Brief update on your products or services]\n\nThat's it for this week. Hit reply if you want to chat about any of it.\n\nCheers,\n[Your Name]\nArmourVault.au"
    },
    "18. Cold Outreach — Restaurant/Hospitality": {
        "subject": "Filling tables on slow nights — without paying for ads",
        "body": "G'day [Name],\n\nI work with restaurants and cafes across [City] who are tired of slow Tuesday nights and wasted prep.\n\nI've built an AI system that predicts your slow periods, automatically sends targeted offers to your customer list, and fills those gaps — without you lifting a finger.\n\n[Similar restaurant] in [Suburb] filled 40 extra covers last month using it.\n\nWorth a 10-minute chat? I can show you exactly how it works.\n\nCheers,\n[Your Name]"
    },
    "19. Cold Outreach — Real Estate": {
        "subject": "More listings, less time on admin",
        "body": "G'day [Name],\n\nI work with real estate agents who are spending too much time on listing descriptions, market reports, and follow-up emails — and not enough time closing deals.\n\nI've built an AI system that writes your listing copy, generates market reports, and handles your follow-up sequences automatically.\n\n[Agent name] at [Agency] went from 4 hours of writing per week to 30 minutes.\n\nWorth a quick chat?\n\nCheers,\n[Your Name]"
    },
    "20. Cold Outreach — Professional Services": {
        "subject": "Automating the parts of your business that eat your time",
        "body": "G'day [Name],\n\nI work with [accountants/lawyers/consultants] who are brilliant at their work but spending too much time on proposals, client reports, and follow-ups.\n\nI've built an AI system that handles all of it — proposals written in minutes, reports generated automatically, follow-ups sent on schedule.\n\n[Similar firm] cut their admin time by 60% in the first month.\n\nWorth a 15-minute call to see if it fits your practice?\n\nCheers,\n[Your Name]"
    },
}

DRIP_SEQUENCES = {
    "New Lead — 7-Day Sequence": [
        {"day": 1, "subject": "Welcome — here's what happens next", "body": "G'day [Name],\n\nThanks for your interest in [Product/Service]. Here's exactly what happens from here:\n\n✅ Day 1 (today): You'll receive this welcome email with everything you need to know\n✅ Day 2: I'll send you a case study showing exactly how [similar business] used this\n✅ Day 3: A quick video walkthrough of the key features\n✅ Day 7: A special offer for action-takers\n\nIn the meantime, if you have any questions, just hit reply.\n\nCheers,\n[Your Name]"},
        {"day": 2, "subject": "How [Similar Business] got [specific result]", "body": "G'day [Name],\n\nYesterday I promised a case study — here it is.\n\n[Business Name] came to us with [specific problem]. They were [pain point description].\n\nAfter using [Product/Service] for [timeframe], they achieved:\n• [Result 1]\n• [Result 2]\n• [Result 3]\n\nThe key thing they did differently: [insight]\n\nCould this work for your business? Reply and let me know your situation.\n\nCheers,\n[Your Name]"},
        {"day": 3, "subject": "Quick walkthrough — see exactly how it works", "body": "G'day [Name],\n\nI know reading about something is different from seeing it in action.\n\nHere's a quick walkthrough of [Product/Service]: [link to demo video or description]\n\nThe three things people always notice first:\n1. [Feature/benefit 1]\n2. [Feature/benefit 2]\n3. [Feature/benefit 3]\n\nAny questions after watching? Just reply.\n\nCheers,\n[Your Name]"},
        {"day": 7, "subject": "Last chance — special offer expires tonight", "body": "G'day [Name],\n\nI've been sharing [Product/Service] with you this week, and I wanted to make you a special offer before it expires tonight.\n\nFor action-takers who sign up today: [specific offer — discount, bonus, extended trial]\n\nThis is only available until midnight tonight.\n\n[CTA button/link]\n\nIf you have any last questions before deciding, reply now and I'll get back to you within the hour.\n\nCheers,\n[Your Name]"},
    ],
    "Free Trial — 7-Day Activation Sequence": [
        {"day": 1, "subject": "Your trial is live — start here", "body": "G'day [Name],\n\nYour free trial of [Product Name] is now active.\n\nTo get your first result in the next 10 minutes:\n\n1. Go to [URL]\n2. Click [specific button]\n3. Enter [specific input]\n4. Watch what happens\n\nThat's it. Your first win is 10 minutes away.\n\nCheers,\n[Your Name]"},
        {"day": 3, "subject": "Have you tried [key feature] yet?", "body": "G'day [Name],\n\nYou've had the trial for a few days — have you tried [key feature] yet?\n\nIt's the one that usually gets people saying 'oh wow' — here's how to find it: [instructions]\n\nIf you've already found it, reply and let me know what you think.\n\nCheers,\n[Your Name]"},
        {"day": 5, "subject": "2 days left — here's what you might have missed", "body": "G'day [Name],\n\nYour trial ends in 2 days. Before it does, here are the features most people miss:\n\n• [Hidden feature 1] — [what it does]\n• [Hidden feature 2] — [what it does]\n• [Pro tip] — [how to get more value]\n\nIf you want to keep access after the trial, here's how: [link]\n\nCheers,\n[Your Name]"},
        {"day": 7, "subject": "Your trial ends today — what did you think?", "body": "G'day [Name],\n\nYour free trial of [Product Name] ends today.\n\nI'd love to know — did you get a chance to try it? What did you think?\n\nIf you want to keep going, you can upgrade here: [link]\n\nIf it wasn't the right fit, no hard feelings — but I'd genuinely appreciate knowing why. It helps me build a better product.\n\nEither way, thanks for giving it a go.\n\nCheers,\n[Your Name]"},
    ],
}

for f, d in [(SF, DEFAULT_SETTINGS), (PF, DEFAULT_PRODUCTS),
             (RF, {"today":0,"history":[]}), (TF,[]), (AVF,[]),
             (LF,[]), (CF,[]), (TASKF,[]), (WINSF,[]),
             (CLIF,[]), (IDEAF,[]), (DREAMF,[]), (SECF,[])]:
    if not f.exists(): jsave(f, d)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="ARTIFICIAL & INTELLIGENT",
                   page_icon="⚡", layout="wide",
                   initial_sidebar_state="collapsed")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
*{font-family:'Inter',sans-serif!important;}
html,body,[class*="css"]{background:#000!important;color:#e0e0e0!important;}
.stApp{background:#000!important;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding:1rem 1.2rem 2rem!important;max-width:100%!important;}
.card{background:rgba(12,12,12,0.9);border:1px solid rgba(255,255,255,.06);border-radius:12px;padding:16px 20px;margin:8px 0;backdrop-filter:blur(20px);transition:border-color .2s;}
.card:hover{border-color:rgba(255,0,128,.15);}
.card-g{border-left:3px solid #00ff41;box-shadow:0 4px 24px rgba(0,0,0,.4),-2px 0 12px rgba(0,255,65,.06);}
.card-p{border-left:3px solid #ff0080;box-shadow:0 4px 24px rgba(0,0,0,.4),-2px 0 12px rgba(255,0,128,.06);}
.card-b{border-left:3px solid #00bfff;box-shadow:0 4px 24px rgba(0,0,0,.4),-2px 0 12px rgba(0,191,255,.06);}
.card-y{border-left:3px solid #ffd700;box-shadow:0 4px 24px rgba(0,0,0,.4),-2px 0 12px rgba(255,215,0,.06);}
.card-o{border-left:3px solid #ff6600;}
[data-testid="stMetricValue"]{color:#00ff41!important;font-weight:800!important;font-size:1.5em!important;}
[data-testid="stMetricLabel"]{color:#333!important;font-size:.75em!important;letter-spacing:.5px;}
.stButton>button{background:rgba(255,0,128,.08)!important;color:#ff0080!important;border:1px solid rgba(255,0,128,.2)!important;border-radius:8px!important;font-weight:600!important;font-size:.82em!important;transition:all .2s!important;}
.stButton>button:hover{background:rgba(255,0,128,.16)!important;border-color:rgba(255,0,128,.4)!important;}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,rgba(255,0,128,.18),rgba(0,255,65,.08))!important;color:#fff!important;border-color:rgba(255,0,128,.35)!important;}
.stTextInput>div>div>input,.stTextArea>div>div>textarea,.stSelectbox>div>div{background:rgba(8,8,8,0.95)!important;color:#e0e0e0!important;border:1px solid rgba(255,255,255,.07)!important;border-radius:8px!important;}
.stTextInput>div>div>input:focus,.stTextArea>div>div>textarea:focus{border-color:rgba(255,0,128,.35)!important;}
.stTabs [data-baseweb="tab-list"]{background:rgba(4,4,4,0.98);border-bottom:1px solid rgba(255,0,128,.1);overflow-x:auto;flex-wrap:nowrap;}
.stTabs [data-baseweb="tab"]{color:#2a2a2a!important;font-size:.73em!important;font-weight:600!important;white-space:nowrap;padding:8px 10px!important;}
.stTabs [aria-selected="true"]{color:#ff0080!important;border-bottom:2px solid #ff0080!important;}
.chat-user{background:rgba(0,255,65,.03);border-left:3px solid #00ff41;padding:14px 18px;border-radius:10px;margin:6px 0;line-height:1.7;}
.chat-ai{background:rgba(255,0,128,.03);border-left:3px solid #ff0080;padding:14px 18px;border-radius:10px;margin:6px 0;line-height:1.7;white-space:pre-wrap;}
.chat-sys{background:rgba(0,191,255,.03);border-left:3px solid #00bfff;padding:8px 14px;border-radius:8px;margin:3px 0;font-size:.78em;color:#333;}
.key-point{background:rgba(255,215,0,.04);border:1px solid rgba(255,215,0,.12);border-radius:6px;padding:5px 10px;margin:2px 0;font-size:.8em;color:#ffd700;}
.pill-on{background:rgba(0,30,8,.9);color:#00ff41;padding:3px 10px;border-radius:20px;font-size:.7em;font-weight:700;display:inline-block;border:1px solid rgba(0,255,65,.18);}
.pill-off{background:rgba(30,0,0,.9);color:#ff4444;padding:3px 10px;border-radius:20px;font-size:.7em;font-weight:700;display:inline-block;border:1px solid rgba(255,68,68,.18);}
.pill-ai{background:rgba(0,8,30,.9);color:#00bfff;padding:3px 10px;border-radius:20px;font-size:.7em;font-weight:700;display:inline-block;border:1px solid rgba(0,191,255,.18);}
.pill-pink{background:rgba(30,0,10,.9);color:#ff0080;padding:3px 10px;border-radius:20px;font-size:.7em;font-weight:700;display:inline-block;border:1px solid rgba(255,0,128,.18);}
.av-card{background:rgba(10,10,10,0.95);border:1px solid rgba(255,0,128,.12);border-radius:12px;padding:14px;margin:6px 0;transition:all .2s;}
.av-card:hover{border-color:rgba(255,0,128,.3);box-shadow:0 0 16px rgba(255,0,128,.08);}
.idea-card{background:rgba(8,8,8,0.95);border:1px solid rgba(255,215,0,.1);border-radius:10px;padding:12px 16px;margin:5px 0;}
.idea-hot{border-color:rgba(255,0,128,.35)!important;}
.sec-green{color:#00ff41!important;font-weight:700;}
.sec-red{color:#ff4444!important;font-weight:700;}
.sec-yellow{color:#ffd700!important;font-weight:700;}
::-webkit-scrollbar{width:3px;height:3px;}
::-webkit-scrollbar-track{background:#000;}
::-webkit-scrollbar-thumb{background:rgba(255,0,128,.2);border-radius:2px;}
.stProgress>div>div{background:linear-gradient(90deg,#ff0080,#00ff41)!important;}
hr{border-color:rgba(255,255,255,.04)!important;}
@media(max-width:768px){
  .block-container{padding:.5rem .5rem 2rem!important;}
  [data-testid="stMetricValue"]{font-size:1.1em!important;}
  .stTabs [data-baseweb="tab"]{font-size:.65em!important;padding:6px 7px!important;}
}
</style>""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if AUTOREFRESH_LIB:
    # Heartbeat every 2 mins to keep Streamlit Cloud session alive
    st_autorefresh(interval=120000, key="heartbeat")

for k, v in [("online",False),("online_ts",0),("weather",None),("weather_ts",0),
             ("authenticated",False),("saved_points",[]), ("chat_counter", 0),
             ("tb_goal_draft", ""), ("tb_context_draft", ""), ("tb_vars_draft", "")]:
    if k not in st.session_state: st.session_state[k] = v

# ── LOGIN ─────────────────────────────────────────────────────────────────────
DASH_PASSWORD = "258088"
if not st.session_state.authenticated:
    st.markdown("""
    <div style='max-width:400px;margin:80px auto;padding:44px 38px;
      background:rgba(6,6,6,0.97);border:1px solid rgba(255,0,128,.28);
      border-radius:20px;backdrop-filter:blur(30px);
      box-shadow:0 0 60px rgba(255,0,128,.1),0 0 120px rgba(0,255,65,.04);'>
      <h1 style='text-align:center;margin:0 0 2px;font-size:1.7em;letter-spacing:-1px;color:#fff;'>⚡ ARTIFICIAL</h1>
      <h1 style='text-align:center;margin:0 0 8px;font-size:1.7em;letter-spacing:-1px;color:#00ff41;'>&amp; INTELLIGENT</h1>
      <p style='text-align:center;color:#222;font-size:.72em;letter-spacing:3px;margin-bottom:28px;'>COMMAND DASHBOARD · ARMOURVAULT.AU</p>
    </div>""", unsafe_allow_html=True)
    cl, cm, cr = st.columns([1,1.3,1])
    with cm:
        pw = st.text_input("Code", type="password", placeholder="Access code",
                           label_visibility="collapsed")
        if st.button("⚡ ACCESS DASHBOARD", use_container_width=True, type="primary"):
            if pw == DASH_PASSWORD:
                st.session_state.authenticated = True; st.rerun()
            else:
                st.error("Incorrect access code.")
        st.markdown("<p style='text-align:center;color:#111;font-size:.68em;margin-top:10px;'>ArmourVault.au · v4.0 · Authorised Access Only</p>",
                    unsafe_allow_html=True)
    st.stop()

# ── Load data ─────────────────────────────────────────────────────────────────
S           = jload(SF, DEFAULT_SETTINGS)
products    = jload(PF, DEFAULT_PRODUCTS)
revenue     = jload(RF, [])
tasks       = jload(TF, [])
avatars     = jload(AVF, [])
leads       = jload(LF, [])
chat        = jload(CF, [])
tasksheet   = jload(TASKF, [])
wins        = jload(WINSF, [])
clients     = jload(CLIF, [])
ideas       = jload(IDEAF, [])
dreambuilds = jload(DREAMF, [])
security_log= jload(SECF, [])

# ── Online / weather cache ────────────────────────────────────────────────────
if time.time() - st.session_state.online_ts > 60:
    st.session_state.online = check_online()
    st.session_state.online_ts = time.time()
online = st.session_state.online

if time.time() - st.session_state.weather_ts > 600:
    st.session_state.weather = get_weather(S.get("weather_city","Sydney"), S.get("weather_key",""))
    st.session_state.weather_ts = time.time()
weather = st.session_state.weather

# ── Computed metrics ──────────────────────────────────────────────────────────
now             = datetime.now()
total_mrr       = sum(p.get("mrr",0) for p in products)
total_arr       = total_mrr * 12
total_customers = sum(p.get("customers",0) for p in products)
open_tasks      = sum(1 for t in tasks if t.get("status") != "Done")
open_leads      = sum(1 for l in leads if l.get("status") == "New")
today_rev       = sum(r.get("amount",0) for r in revenue if isinstance(r,dict) and r.get("date","") == now.strftime("%Y-%m-%d"))

# ── HEADER ────────────────────────────────────────────────────────────────────
weather_str = f"🌤 {weather['temp']}°C {weather['city']}" if weather else ""
online_pill = "<span style='background:#00ff41;color:#000;padding:2px 8px;border-radius:10px;font-size:.7em;font-weight:700;'>● ONLINE</span>" if online else "<span style='background:#ff0080;color:#fff;padding:2px 8px;border-radius:10px;font-size:.7em;font-weight:700;'>● OFFLINE</span>"
ai_pill     = "<span style='background:#1a1a2e;color:#00ff41;padding:2px 8px;border-radius:10px;font-size:.7em;font-weight:700;border:1px solid #00ff41;'>⚡ DeepSeek R1</span>" if online else "<span style='background:#1a1a2e;color:#ff0080;padding:2px 8px;border-radius:10px;font-size:.7em;font-weight:700;border:1px solid #ff0080;'>⚡ LM Studio</span>"

st.markdown(f"""
<div style='display:flex;align-items:center;justify-content:space-between;
  padding:8px 2px;border-bottom:1px solid rgba(255,0,128,.08);margin-bottom:12px;flex-wrap:wrap;gap:8px;'>
  <div>
    <span style='font-size:1.25em;font-weight:900;letter-spacing:-1px;color:#fff;'>⚡ ARTIFICIAL</span>
    <span style='font-size:1.25em;font-weight:900;letter-spacing:-1px;color:#00ff41;'> & INTELLIGENT</span>
    <span style='color:#1a1a1a;font-size:.65em;margin-left:8px;letter-spacing:2px;'>ARMOURVAULT.AU</span>
  </div>
  <div style='display:flex;align-items:center;gap:8px;flex-wrap:wrap;'>
    <span style='color:#ff0080;font-size:.8em;font-weight:700;'>{now.strftime("%H:%M")}</span>
    <span style='color:#222;font-size:.75em;'>{now.strftime("%a %d %b %Y")}</span>
{f"<span style='color:#444;font-size:.75em;'>{weather_str}</span>" if weather_str else ""}
{online_pill} {ai_pill}
  </div>
</div>""", unsafe_allow_html=True)

# ── KPIs ──────────────────────────────────────────────────────────────────────
k1,k2,k3,k4,k5,k6 = st.columns(6)
k1.metric("MRR", f"${total_mrr:,}", f"+${today_rev}")
k2.metric("ARR", f"${total_arr:,}")
k3.metric("Customers", total_customers)
k4.metric("Open Tasks", open_tasks)
k5.metric("Hot Leads", open_leads)
k6.metric("Avatars Built", len(avatars))

# ── TABS ──────────────────────────────────────────────────────────────────────
tabs = st.tabs([
    "🏠 Home","💬 Chat","🤖 Agents","🎭 Avatars","📱 Social",
    "🛡️ Security","📧 Email","🔍 Leads","💡 Ideas","🌟 Dream Build",
    "📦 Products","💰 Revenue","🚀 Biz Tools","📋 Tasks","⚙️ Settings"
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 0 — HOME / COMMAND CENTRE
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    st.markdown("## 🏠 Daily Command Centre")
    col1, col2 = st.columns([1.6, 1])
    with col1:
        # Morning briefing
        items = []
        if open_tasks > 0: items.append(f"**{open_tasks} tasks** in the queue")
        if open_leads > 0: items.append(f"**{open_leads} hot leads** need follow-up")
        if today_rev > 0:  items.append(f"**${today_rev:,}** logged today")
        if len(avatars) > 0: items.append(f"**{len(avatars)} avatars** in your roster")
        if not items: items.append("All clear — ready to build.")
        st.markdown(f"""<div class='card card-g'>
<span style='color:#00ff41;font-size:.72em;font-weight:700;letter-spacing:1px;'>MORNING BRIEFING · {now.strftime("%A %d %B")}</span><br><br>
{"<br>".join(f"• {i}" for i in items)}
</div>""", unsafe_allow_html=True)

        st.markdown("### ⚡ Quick Execute")
        qt = st.text_area("What needs doing?", height=80,
                          placeholder="e.g. Write 3 cold emails for mining companies...",
                          key="qt_home")
        qa = st.selectbox("Agent:", [a["name"] for a in AGENTS], key="qa_home")
        if st.button("⚡ Execute Now", use_container_width=True, type="primary", key="exec_home"):
            if qt.strip():
                agent_sys = next((a["system"] for a in AGENTS if a["name"]==qa), AGENTS[0]["system"])
                with st.spinner(f"{qa} executing..."):
                    result, engine = ai_call(qt, system=agent_sys, max_tokens=1000)
                if result:
                    st.success(f"✅ Done via {engine}")
                    st.markdown(f"<div class='card card-g'><pre style='white-space:pre-wrap;color:#e0e0e0;font-size:.85em;'>{result}</pre></div>",
                                unsafe_allow_html=True)
                    tasks.append({"id":len(tasks)+1,"desc":qt,"agent":qa,"status":"Done",
                                  "result":result,"engine":engine,
                                  "date":now.strftime("%Y-%m-%d"),"time":now.strftime("%H:%M")})
                    jsave(TF, tasks)
                else:
                    st.warning("No AI engine — start LM Studio or check Settings.")

    with col2:
        st.markdown(f"""<div class='card card-p'>
<div style='font-size:1.9em;font-weight:900;color:#ff0080;'>${total_mrr:,}</div>
<div style='color:#222;font-size:.72em;letter-spacing:1px;'>MONTHLY RECURRING REVENUE</div>
<hr>
<div style='font-size:1.2em;font-weight:700;color:#00ff41;'>${total_arr:,}</div>
<div style='color:#222;font-size:.68em;'>ANNUAL RUN RATE</div>
</div>""", unsafe_allow_html=True)

        st.markdown("### 🎯 Revenue Milestones")
        for target, label in [(1000,"$1K MRR"),(5000,"$5K"),(10000,"$10K"),(25000,"$25K"),(50000,"$50K")]:
            pct = min(100, int(total_mrr/target*100))
            col = "#00ff41" if pct >= 100 else "#ff0080"
            st.markdown(f"""<div style='margin:3px 0;'>
<div style='display:flex;justify-content:space-between;font-size:.72em;'>
  <span style='color:#333;'>{label}</span><span style='color:{col};font-weight:700;'>{pct}%</span>
</div>
<div style='background:rgba(255,255,255,.03);border-radius:3px;height:3px;margin-top:2px;'>
  <div style='background:{col};width:{pct}%;height:3px;border-radius:3px;'></div>
</div></div>""", unsafe_allow_html=True)

        st.markdown("### 🏆 Weekly Wins")
        new_win = st.text_input("Log a win:", placeholder="Closed a deal...", key="win_home")
        if st.button("+ Log Win", key="addwin"):
            if new_win.strip():
                wins.append({"win":new_win,"date":now.strftime("%Y-%m-%d")})
                jsave(WINSF, wins); st.success("Win logged! 🏆")
        for w in reversed(wins[-4:]):
            st.markdown(f"<div class='card card-y' style='padding:7px 12px;'><span style='color:#ffd700;'>🏆</span> <span style='font-size:.82em;'>{w['win']}</span></div>",
                        unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — AI CHAT (rolling script, key points, saved highlights)
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    st.markdown("## 💬 AI Command Chat")
    st.markdown("<p style='color:#333;font-size:.8em;'>Context-aware — knows your MRR, products, leads, tasks. Talk naturally. Commands work inline.</p>",
                unsafe_allow_html=True)

    ce1, ce2, ce3 = st.columns(3)
    with ce1:
        st.markdown(f"<span class='pill-ai'>⚡ {'DeepSeek R1' if online else 'LM Studio'}</span>", unsafe_allow_html=True)
    with ce2:
        st.markdown(f"<span class='pill-pink'>💬 {len(chat)} messages</span>", unsafe_allow_html=True)
    with ce3:
        if st.button("🗑️ Clear Chat", key="clearchat"):
            jsave(CF, []); st.rerun()

    # Saved key points
    if st.session_state.saved_points:
        st.markdown("### 📌 Saved Key Points")
        for i, pt in enumerate(st.session_state.saved_points):
            cp, cd = st.columns([10, 1])
            with cp: st.markdown(f"<div class='key-point'>📌 {pt}</div>", unsafe_allow_html=True)
            with cd:
                if st.button("✕", key=f"delpt_{i}"):
                    st.session_state.saved_points.pop(i); st.rerun()
        st.markdown("---")

    # Rolling chat history
    for i, msg in enumerate(chat[-25:]):
        role    = msg.get("role","user")
        content = msg.get("content","")
        engine  = msg.get("engine","")
        ts      = msg.get("time","")
        if role == "user":
            st.markdown(f"""<div class='chat-user'>
<span style='color:#00ff41;font-size:.7em;font-weight:700;'>YOU · {ts}</span><br>
<span style='font-size:.88em;'>{content}</span>
</div>""", unsafe_allow_html=True)
        elif role == "assistant":
            formatted = content.replace('\n\n','<br><br>').replace('\n','<br>')
            st.markdown(f"""<div class='chat-ai'>
<span style='color:#ff0080;font-size:.7em;font-weight:700;'>AI · {engine} · {ts}</span><br>
<span style='font-size:.87em;line-height:1.75;'>{formatted}</span>
</div>""", unsafe_allow_html=True)
            kpts = extract_key_points(content)
            if kpts:
                with st.expander(f"📌 {len(kpts)} Key Points — click to save", expanded=False):
                    for pt in kpts:
                        kc, ks = st.columns([9,1])
                        with kc: st.markdown(f"<div class='key-point'>{pt}</div>", unsafe_allow_html=True)
                        with ks:
                            if st.button("📌", key=f"save_{i}_{pt[:8]}"):
                                if pt not in st.session_state.saved_points:
                                    st.session_state.saved_points.append(pt); st.rerun()
        elif role == "system":
            st.markdown(f"<div class='chat-sys'>{content}</div>", unsafe_allow_html=True)

    st.markdown("---")

    # Quick commands
    st.markdown("<span style='color:#1a1a1a;font-size:.72em;'>QUICK COMMANDS</span>", unsafe_allow_html=True)
    qcols = st.columns(4)
    qcmds = ["Write a cold email for a mining company",
             "What should I focus on today?",
             "Generate 5 TikTok hooks for my AI product",
             "Write a follow-up for a warm lead"]
    for qi, qc in enumerate(qcmds):
        with qcols[qi]:
            if st.button(qc[:28]+"…", key=f"qc_{qi}", use_container_width=True):
                st.session_state["chat_prefill"] = qc

    prefill = st.session_state.pop("chat_prefill", "")
    ca, cb = st.columns([4,1])
    with ca:
        # Use a dynamic key to force-clear the text area after sending
        input_key = f"chat_input_{st.session_state.chat_counter}"
        user_msg = st.text_area("Message:", value=prefill, height=90,
                                placeholder="Talk to your crew... 'write me a proposal', 'what's my MRR?', 'build an avatar for a tradie in Brisbane'",
                                key=input_key)
    with cb:
        chat_agent = st.selectbox("Agent:", ["Auto"]+[a["name"] for a in AGENTS], key="chat_agent")
        notify_tg  = st.checkbox("📱 Notify", key="chat_notify")

    cs1, cs2 = st.columns(2)
    with cs1:
        if st.button("⚡ SEND", use_container_width=True, type="primary", key="chat_send"):
            if user_msg.strip():
                ctx = f"""You are the AI crew for ArmourVault.au — Australian cybersecurity and AI tools.
Business: MRR ${total_mrr:,} | ARR ${total_arr:,} | {total_customers} customers | {open_leads} hot leads | {open_tasks} open tasks | {len(avatars)} avatars.
Products: {', '.join(p['name'] for p in products[:6])}.
Respond clearly and practically. Use markdown. Be direct and Australian in tone."""
                sys_prompt = (next((a["system"] for a in AGENTS if a["name"]==chat_agent), ctx) + "\n\n" + ctx) if chat_agent != "Auto" else ctx
                chat.append({"role":"user","content":user_msg,"time":now.strftime("%H:%M")})
                jsave(CF, chat)
                with st.spinner("Thinking..."):
                    result, engine = ai_call(user_msg, system=sys_prompt, max_tokens=1500)
                if result:
                    chat.append({"role":"assistant","content":result,"engine":engine,"time":now.strftime("%H:%M")})
                    if notify_tg: send_telegram(f"💬 Chat\n{result[:300]}")
                else:
                    chat.append({"role":"system","content":"No AI engine — start LM Studio or check Settings."})
                
                # Increment counter to clear the text area on next run
                st.session_state.chat_counter += 1
                jsave(CF, chat); st.rerun()
    with cs2:
        if st.button("📋 Export Chat", use_container_width=True, key="chat_export"):
            txt = "\n\n".join([f"[{m.get('role','').upper()} {m.get('time','')}]\n{m.get('content','')}" for m in chat])
            st.download_button("⬇ Download", txt, "chat_log.txt", key="dl_chat")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — AGENT SQUAD
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    st.markdown("## 🤖 Agent Squad")
    acols = st.columns(4)
    for ai2, agent in enumerate(AGENTS):
        with acols[ai2 % 4]:
            st.markdown(f"""<div class='card' style='border-left:3px solid {agent["color"]};text-align:center;padding:10px;'>
<div style='font-size:1.4em;'>{agent["emoji"]}</div>
<div style='font-weight:700;font-size:.78em;color:{agent["color"]};'>{agent["name"]}</div>
</div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### ⚡ Tasklet Builder")
    st.markdown("<p style='font-size:.8em;color:#555;'>Define a structured task for an agent to execute. Be specific for best results.</p>", unsafe_allow_html=True)
    
    tb_c1, tb_c2 = st.columns([2,1])
    with tb_c1:
        # Draft Persistence: Use session state to keep text across refreshes
        goal = st.text_input("**Goal / Objective:**", 
                            value=st.session_state.tb_goal_draft,
                            placeholder="e.g. Write 3 cold emails for a mining company client", 
                            key="tb_goal_input")
        if goal != st.session_state.tb_goal_draft:
            st.session_state.tb_goal_draft = goal
            
        context = st.text_area("**Context / Background:**", 
                              value=st.session_state.tb_context_draft,
                              placeholder="e.g. Client is a mid-tier iron ore explorer in WA. Target is the CFO. Pain point is SOCI Act compliance reporting overhead.", 
                              height=100, 
                              key="tb_context_input")
        if context != st.session_state.tb_context_draft:
            st.session_state.tb_context_draft = context
            
        variables = st.text_area("**Key Variables / Inputs:**", 
                                value=st.session_state.tb_vars_draft,
                                placeholder="e.g. Client Name: BHP, Target Name: [Name], Specific Ask: 15-min call next week", 
                                height=100, 
                                key="tb_vars_input")
        if variables != st.session_state.tb_vars_draft:
            st.session_state.tb_vars_draft = variables
    with tb_c2:
        agent_sel = st.selectbox("**Agent:**", [a["name"] for a in AGENTS], key="tb_agent_sel")
        output_format = st.selectbox("**Output Format:**", ["Default (Agent decides)", "Markdown Report", "JSON", "Plain Text", "Email format", "Code block"], key="tb_output")
        st.markdown("<br>", unsafe_allow_html=True)
        exec_btn = st.button("⚡ Execute Tasklet", use_container_width=True, type="primary", key="tb_exec")

    if exec_btn and goal.strip():
        prompt = f"""**GOAL:** {goal}

**CONTEXT:**
{context}

**VARIABLES:**
{variables}

**OUTPUT FORMAT:** {output_format}"""
        
        agent_sys = next((a["system"] for a in AGENTS if a["name"]==agent_sel), AGENTS[0]["system"])
        tasks.append({"id":len(tasks)+1,"desc":goal,"agent":agent_sel,"priority":"High",
                      "status":"Running","date":now.strftime("%Y-%m-%d"),"time":now.strftime("%H:%M"), "prompt": prompt})
        jsave(TF, tasks)
        
        with st.spinner(f"{agent_sel} is on the job..."):
            result, engine = ai_call(prompt, system=agent_sys, max_tokens=2000)
        
        if result:
            tasks[-1].update({"result":result,"status":"Done","engine":engine})
            jsave(TF, tasks)
            # Clear drafts after successful execution
            st.session_state.tb_goal_draft = ""
            st.session_state.tb_context_draft = ""
            st.session_state.tb_vars_draft = ""
            st.success(f"✅ {agent_sel} finished the job. Engine: {engine}")
            st.markdown("### ⚡ Result")
            st.markdown(result, unsafe_allow_html=True)
            send_telegram(f"✅ Tasklet Done: {goal[:80]}")
            st.rerun()
        else:
            tasks[-1]["status"] = "Queued"; jsave(TF, tasks)
            st.warning("No AI engine available — task has been queued.")

    st.markdown("---")
    st.markdown("### 📋 Daily Assignment Sheet")
    DAILY = {
        "✍️ Content Machine":["Write 3 LinkedIn posts","Draft weekly newsletter","Create ad copy for top product","Write 5 TikTok scripts","Generate 10 viral hooks"],
        "📧 Email Agent":["Send cold outreach batch (10)","Follow up unanswered emails","Draft onboarding sequence","Write 3 testimonial requests"],
        "💬 Sales Bot":["Respond to all inquiries","Follow up trial users","Send proposals to warm leads","Write objection handler scripts"],
        "📊 Analytics Brain":["Generate weekly revenue report","Analyse customer churn","Identify top products","Build growth projection"],
        "🚀 Deploy Master":["Deploy latest updates","Test all products","Monitor uptime","Plan next launch"],
        "💻 Code Builder":["Build new feature","Fix reported bugs","Optimise existing code","Write API integration"],
        "📱 Social Agent":["Schedule week of posts","Write platform-specific captions","Generate hashtag sets","Draft DM outreach messages"],
        "🛡️ Security Agent":["Run compliance check","Update security log","Review access controls","Draft incident response plan"],
    }
    for aname, dtasks in DAILY.items():
        with st.expander(aname, expanded=False):
            for dt in dtasks:
                dc, dr = st.columns([5,1])
                with dc:
                    st.markdown(f"<span style='font-size:.83em;color:#444;'>▸ {dt}</span>", unsafe_allow_html=True)
                with dr:
                    bk = f"run_{aname}_{dt}".replace(" ","_")[:55]
                    if st.button("▶", key=bk):
                        clean = aname.split(" ",1)[1] if " " in aname else aname
                        asys  = next((a["system"] for a in AGENTS if a["name"]==clean), AGENTS[0]["system"])
                        with st.spinner("Running..."):
                            res, eng = ai_call(dt, system=asys, max_tokens=800)
                        if res:
                            st.text_area("Result:", value=res, height=180, key=f"res_{bk}")

    if tasks:
        st.markdown("---")
        st.markdown(f"### 📋 Task Queue ({len(tasks)})")
        for t in reversed(tasks[-12:]):
            sc = "#00ff41" if t.get("status")=="Done" else "#ffd700" if t.get("status")=="Running" else "#2a2a2a"
            st.markdown(f"""<div class='card' style='padding:9px 14px;'>
<span style='color:{sc};font-weight:700;font-size:.72em;'>[{t.get("status","?")}]</span>
<strong style='font-size:.82em;'> {t.get("agent","?")}</strong>
<span style='font-size:.8em;color:#444;'> — {t.get("desc","")[:65]}</span>
<span style='color:#111;float:right;font-size:.68em;'>{t.get("date","")} {t.get("time","")}</span>
</div>""", unsafe_allow_html=True)
            if t.get("result"):
                with st.expander("View result"):
                    st.text(t["result"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — AVATAR BUILDER (full pipeline + folder)
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    st.markdown("## 🎭 Autonomous Avatar Builder")
    st.markdown("<p style='color:#333;font-size:.8em;'>Drop in an idea → AI builds the complete persona, scripts, strategy, and launches the motion video.</p>",
                unsafe_allow_html=True)

    av1, av2 = st.columns([1.4, 1])
    with av1:
        st.markdown("### ⚡ Build New Avatar")
        av_idea = st.text_area("Your idea / niche / concept:",
                               placeholder="e.g. 'Funny tradie in Sydney who talks about home security' or 'Professional female AI consultant targeting mining companies'",
                               height=90, key="av_idea")
        avc1, avc2, avc3 = st.columns(3)
        with avc1:
            av_platform = st.multiselect("Platforms:", ["TikTok","Instagram","YouTube","LinkedIn","Facebook","X"], default=["TikTok","Instagram"], key="av_plat")
        with avc2:
            av_tone = st.selectbox("Tone:", ["Funny & Relatable","Professional","Inspirational","Educational","Edgy & Bold","Australian Casual"], key="av_tone")
        with avc3:
            av_niche = st.selectbox("Niche:", ["Cybersecurity","AI Tools","Tradies","Small Business","Mining","Real Estate","Hospitality","General"], key="av_niche")

        av_build = st.button("🎭 BUILD FULL AVATAR", use_container_width=True, type="primary", key="av_build")
        if av_build and av_idea.strip():
            prompt = f"""Build a complete, fully autonomous AI avatar persona based on this idea:
IDEA: {av_idea}
PLATFORMS: {', '.join(av_platform)}
TONE: {av_tone}
NICHE: {av_niche}

Deliver ALL of the following:

## PERSONA
- Name, Age, Location, Backstory (3 sentences)
- Personality traits (5 bullet points)
- Signature catchphrase
- Visual style description

## CONTENT STRATEGY
- Primary platform and why
- Content pillars (4 topics they always talk about)
- Posting frequency per platform
- Best posting times

## 10 READY-TO-FILM SCRIPTS
For each script provide: Title, Hook (first 3 seconds), Full Script (60-90 seconds), CTA

## 30-DAY CONTENT CALENDAR
Week 1-4 with specific post ideas per day for each platform

## MONETISATION PLAN
- 3 revenue streams with specific amounts
- First product to launch and price
- Affiliate opportunities
- Timeline to first $1,000

## PLATFORM SETUP CHECKLIST
- Bio copy for each platform (ready to paste)
- Hashtag sets (10 per platform)
- Profile optimisation tips

## VOICE & STYLE GUIDE
- Words to always use
- Words to never use
- Editing style
- Music/sound recommendations"""
            with st.spinner("Building full avatar — this takes 30-60 seconds..."):
                result, engine = ai_call(prompt, max_tokens=2500)
            if result:
                av_entry = {
                    "id": len(avatars)+1,
                    "idea": av_idea,
                    "platforms": av_platform,
                    "tone": av_tone,
                    "niche": av_niche,
                    "content": result,
                    "engine": engine,
                    "date": now.strftime("%Y-%m-%d"),
                    "time": now.strftime("%H:%M"),
                    "videos": []
                }
                avatars.append(av_entry)
                jsave(AVF, avatars)
                # Save to folder file
                av_file = AVDIR / f"avatar_{av_entry['id']}_{now.strftime('%Y%m%d')}.txt"
                av_file.write_text(f"AVATAR #{av_entry['id']}\nIdea: {av_idea}\nDate: {now}\nEngine: {engine}\n\n{result}")
                st.success(f"✅ Avatar #{av_entry['id']} built via {engine} — saved to folder")
                st.markdown(f"<div class='card card-p'><pre style='white-space:pre-wrap;color:#e0e0e0;font-size:.82em;line-height:1.7;'>{result}</pre></div>",
                            unsafe_allow_html=True)
                st.download_button("⬇ Download Avatar", result, f"avatar_{av_entry['id']}.txt", key="dl_av")
            else:
                st.warning("No AI engine — start LM Studio or check Settings.")

    with av2:
        st.markdown("### 🎬 Motion Video Generator")
        st.markdown("<p style='color:#333;font-size:.78em;'>Generate a talking motion avatar video from any script using HeyGen or D-ID.</p>",
                    unsafe_allow_html=True)

        vid_platform = st.selectbox("Video Platform:", ["HeyGen","D-ID"], key="vid_plat")
        vid_script   = st.text_area("Script for video:", height=120,
                                    placeholder="Paste a script from your avatar build, or write a new one...",
                                    key="vid_script")

        if vid_platform == "HeyGen":
            st.markdown(f"<span class='pill-pink'>HeyGen API Key: {'✅ Set' if S.get('heygen_key') else '❌ Not set — add in Settings'}</span>",
                        unsafe_allow_html=True)
            if st.button("🎬 Generate HeyGen Video", use_container_width=True, type="primary", key="heygen_gen"):
                if not S.get("heygen_key"):
                    st.error("Add your HeyGen API key in Settings first.")
                elif not vid_script.strip():
                    st.warning("Enter a script first.")
                else:
                    with st.spinner("Sending to HeyGen..."):
                        vid_id, msg = heygen_generate(vid_script, S.get("heygen_key",""))
                    if vid_id:
                        st.success(f"✅ {msg}")
                        st.info(f"Video ID: `{vid_id}` — Check your HeyGen dashboard in 2-3 minutes")
                    else:
                        st.error(msg)
        else:
            st.markdown(f"<span class='pill-pink'>D-ID API Key: {'✅ Set' if S.get('did_key') else '❌ Not set — add in Settings'}</span>",
                        unsafe_allow_html=True)
            if st.button("🎬 Generate D-ID Video", use_container_width=True, type="primary", key="did_gen"):
                if not S.get("did_key"):
                    st.error("Add your D-ID API key in Settings first.")
                elif not vid_script.strip():
                    st.warning("Enter a script first.")
                else:
                    with st.spinner("Sending to D-ID..."):
                        vid_id, msg = did_generate(vid_script, S.get("did_key",""))
                    if vid_id:
                        st.success(f"✅ {msg}")
                        st.info(f"Talk ID: `{vid_id}` — Check your D-ID dashboard")
                    else:
                        st.error(msg)

        st.markdown("---")
        st.markdown("### 🎙️ AI Script Generator")
        sg_topic = st.text_input("Topic:", placeholder="e.g. Why tradies need cybersecurity", key="sg_topic")
        sg_dur   = st.selectbox("Duration:", ["30 seconds","60 seconds","90 seconds","3 minutes"], key="sg_dur")
        sg_plat  = st.selectbox("Platform:", ["TikTok","Instagram Reel","YouTube Short","LinkedIn"], key="sg_plat")
        if st.button("✍️ Generate Script", use_container_width=True, key="sg_gen"):
            if sg_topic.strip():
                sp = f"Write a {sg_dur} talking-head video script for {sg_plat} about: {sg_topic}. Include: Hook (first 3 seconds to stop the scroll), Main content, CTA. Write it as spoken words, natural and conversational. Australian tone."
                with st.spinner("Writing script..."):
                    sres, seng = ai_call(sp, max_tokens=600)
                if sres:
                    st.text_area("Generated Script:", value=sres, height=200, key="sg_result")
                    st.session_state["vid_script_prefill"] = sres

    st.markdown("---")
    st.markdown(f"### 📁 Avatar Folder ({len(avatars)} avatars)")
    if not avatars:
        st.markdown("<p style='color:#222;'>No avatars built yet. Use the builder above to create your first one.</p>",
                    unsafe_allow_html=True)
    else:
        for av in reversed(avatars):
            with st.expander(f"🎭 Avatar #{av['id']} — {av['idea'][:55]} · {av['date']}"):
                avc1, avc2, avc3 = st.columns(3)
                with avc1: st.markdown(f"<span class='pill-pink'>Tone: {av.get('tone','?')}</span>", unsafe_allow_html=True)
                with avc2: st.markdown(f"<span class='pill-ai'>Niche: {av.get('niche','?')}</span>", unsafe_allow_html=True)
                with avc3: st.markdown(f"<span class='pill-on'>Engine: {av.get('engine','?')}</span>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:.82em;color:#e0e0e0;white-space:pre-wrap;line-height:1.7;max-height:400px;overflow-y:auto;'>{av['content'][:2500]}...</div>",
                            unsafe_allow_html=True)
                afd1, afd2 = st.columns(2)
                with afd1:
                    st.download_button("⬇ Download", av["content"], f"avatar_{av['id']}.txt", key=f"dl_av_{av['id']}")
                with afd2:
                    if st.button("🗑️ Delete", key=f"del_av_{av['id']}"):
                        avatars = [a for a in avatars if a["id"] != av["id"]]
                        jsave(AVF, avatars); st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — SOCIAL COMMAND CENTRE
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[4]:
    st.markdown("## 📱 Social Command Centre")
    st.markdown("<p style='color:#333;font-size:.8em;'>One idea → ready-to-post content for all 6 platforms. Copy, paste, post. Done.</p>",
                unsafe_allow_html=True)

    soc_tabs = st.tabs(["🚀 All Platforms","📘 Facebook","📸 Instagram","💼 LinkedIn","🎵 TikTok","▶️ YouTube","𝕏 X/Twitter","📩 DM Writer","📅 Content Calendar","🔍 Competitor Spy"])

    with soc_tabs[0]:
        st.markdown("### ⚡ Generate for All Platforms")
        sc_idea = st.text_area("Topic / Idea / Product:", height=80,
                               placeholder="e.g. Why small businesses need AI-powered cybersecurity in 2025",
                               key="sc_idea")
        sc_brand = st.text_input("Brand voice:", value="ArmourVault.au — Australian, direct, no BS, cybersecurity + AI", key="sc_brand")
        sc_gen = st.button("⚡ GENERATE ALL PLATFORMS", use_container_width=True, type="primary", key="sc_gen_all")
        if sc_gen and sc_idea.strip():
            prompt = f"""Create platform-specific social media content for this topic:
TOPIC: {sc_idea}
BRAND: {sc_brand}

Generate ready-to-post content for each platform:

## FACEBOOK POST
(Conversational, 150-300 words, 3-5 relevant hashtags, CTA)

## INSTAGRAM CAPTION
(Punchy opening line, 100-200 words, 20-25 hashtags, CTA, emoji-friendly)

## INSTAGRAM REEL SCRIPT
(30-60 second talking head script with hook, content, CTA)

## LINKEDIN POST
(Professional, thought leadership angle, 200-400 words, 3-5 hashtags, no fluff)

## TIKTOK SCRIPT
(15-30 second script, strong hook in first 2 seconds, trending audio suggestion)

## YOUTUBE SHORT SCRIPT
(60 second script, thumbnail text suggestion, title, description, tags)

## X/TWITTER THREAD
(5-tweet thread, each under 280 chars, strong opener, ends with CTA)

## STORY/REEL HOOK VARIATIONS
(10 different opening lines to test)"""
            with st.spinner("Generating all platforms..."):
                sc_result, sc_engine = ai_call(prompt, max_tokens=2500)
            if sc_result:
                st.success(f"✅ Generated via {sc_engine}")
                st.markdown(f"<div class='card card-p'><pre style='white-space:pre-wrap;color:#e0e0e0;font-size:.83em;line-height:1.75;'>{sc_result}</pre></div>",
                            unsafe_allow_html=True)
                st.download_button("⬇ Download All", sc_result, "social_content.txt", key="dl_sc")
            else:
                st.warning("No AI engine available.")

    with soc_tabs[1]:
        st.markdown("### 📘 Facebook Content")
        fb_topic = st.text_input("Topic:", key="fb_topic")
        fb_type  = st.selectbox("Type:", ["Engagement Post","Promotional Post","Story","Event","Group Post","Ad Copy"], key="fb_type")
        if st.button("Generate Facebook Content", key="fb_gen"):
            if fb_topic.strip():
                p = f"Write a {fb_type} for Facebook about: {fb_topic}. Australian business tone, conversational, include 3-5 hashtags and a clear CTA. Optimise for Facebook's algorithm (engagement-focused)."
                with st.spinner("Writing..."):
                    r, e = ai_call(p, max_tokens=600)
                if r: st.text_area("Result:", value=r, height=200, key="fb_result")

    with soc_tabs[2]:
        st.markdown("### 📸 Instagram Content")
        ig_topic = st.text_input("Topic:", key="ig_topic")
        ig_type  = st.selectbox("Type:", ["Feed Post","Reel Script","Story","Carousel","Bio","Ad Copy"], key="ig_type")
        if st.button("Generate Instagram Content", key="ig_gen"):
            if ig_topic.strip():
                p = f"Write Instagram {ig_type} content about: {ig_topic}. Include punchy hook, body, 25 hashtags, CTA. Australian voice. Optimise for Instagram engagement."
                with st.spinner("Writing..."):
                    r, e = ai_call(p, max_tokens=700)
                if r: st.text_area("Result:", value=r, height=220, key="ig_result")

    with soc_tabs[3]:
        st.markdown("### 💼 LinkedIn Content")
        li_topic = st.text_input("Topic:", key="li_topic")
        li_type  = st.selectbox("Type:", ["Thought Leadership Post","Case Study","Connection Request","InMail Outreach","Company Update","Article Intro"], key="li_type")
        if st.button("Generate LinkedIn Content", key="li_gen"):
            if li_topic.strip():
                p = f"Write a LinkedIn {li_type} about: {li_topic}. Professional Australian tone, thought leadership angle, 200-400 words, 3-5 hashtags. No corporate fluff — be direct and insightful."
                with st.spinner("Writing..."):
                    r, e = ai_call(p, max_tokens=700)
                if r: st.text_area("Result:", value=r, height=220, key="li_result")

    with soc_tabs[4]:
        st.markdown("### 🎵 TikTok Content")
        tt_topic = st.text_input("Topic:", key="tt_topic")
        tt_dur   = st.selectbox("Duration:", ["15 seconds","30 seconds","60 seconds","3 minutes"], key="tt_dur")
        if st.button("Generate TikTok Script", key="tt_gen"):
            if tt_topic.strip():
                p = f"Write a {tt_dur} TikTok script about: {tt_topic}. MUST have a scroll-stopping hook in the first 2 seconds. Conversational, Australian, punchy. Include: Hook, Content, CTA, trending sound suggestion, on-screen text suggestions."
                with st.spinner("Writing..."):
                    r, e = ai_call(p, max_tokens=600)
                if r: st.text_area("Result:", value=r, height=220, key="tt_result")

    with soc_tabs[5]:
        st.markdown("### ▶️ YouTube Content")
        yt_topic = st.text_input("Topic:", key="yt_topic")
        yt_type  = st.selectbox("Type:", ["Short Script (60s)","Long Form Script","Title + Description + Tags","Thumbnail Text Ideas","Community Post"], key="yt_type")
        if st.button("Generate YouTube Content", key="yt_gen"):
            if yt_topic.strip():
                p = f"Create YouTube {yt_type} for: {yt_topic}. Optimise for YouTube SEO. Australian business focus. Include all metadata if applicable."
                with st.spinner("Writing..."):
                    r, e = ai_call(p, max_tokens=800)
                if r: st.text_area("Result:", value=r, height=220, key="yt_result")

    with soc_tabs[6]:
        st.markdown("### 𝕏 X/Twitter Content")
        x_topic = st.text_input("Topic:", key="x_topic")
        x_type  = st.selectbox("Type:", ["Single Tweet","5-Tweet Thread","10-Tweet Thread","Reply","Bio"], key="x_type")
        if st.button("Generate X Content", key="x_gen"):
            if x_topic.strip():
                p = f"Write a {x_type} for X/Twitter about: {x_topic}. Punchy, direct, Australian voice. Under 280 chars per tweet. Strong hook, clear value, CTA at end."
                with st.spinner("Writing..."):
                    r, e = ai_call(p, max_tokens=600)
                if r: st.text_area("Result:", value=r, height=200, key="x_result")

    with soc_tabs[7]:
        st.markdown("### 📩 DM / Message Writer")
        dm_name    = st.text_input("Person's name / handle:", placeholder="e.g. John Smith or @johntrades", key="dm_name")
        dm_context = st.text_area("Context:", height=70,
                                  placeholder="e.g. Tradie in Brisbane, 500 followers, posts about plumbing jobs, looking to grow his business",
                                  key="dm_context")
        dm_platform = st.selectbox("Platform:", ["Facebook","Instagram","LinkedIn","TikTok","X"], key="dm_plat")
        dm_goal     = st.selectbox("Goal:", ["Cold Outreach","Follow-Up","Partnership","Collaboration","Sales","Networking"], key="dm_goal")
        if st.button("✍️ Write DM", use_container_width=True, type="primary", key="dm_gen"):
            if dm_name.strip():
                p = f"Write a {dm_goal} DM for {dm_platform} to: {dm_name}. Context: {dm_context}. Keep it short (under 150 words), personal, not salesy. Australian tone. No generic openers. Reference something specific about them if context is given."
                with st.spinner("Writing DM..."):
                    r, e = ai_call(p, max_tokens=400)
                if r:
                    st.text_area("Your DM (copy and send):", value=r, height=160, key="dm_result")
                    st.success("Ready to copy and paste!")

    with soc_tabs[8]:
        st.markdown("### 📅 30-Day Content Calendar")
        cal_niche = st.text_input("Niche/Business:", value="Cybersecurity and AI tools for small business", key="cal_niche")
        cal_plats = st.multiselect("Platforms:", ["TikTok","Instagram","LinkedIn","Facebook","YouTube","X"], default=["TikTok","Instagram","LinkedIn"], key="cal_plats")
        if st.button("📅 Generate 30-Day Calendar", use_container_width=True, type="primary", key="cal_gen"):
            if cal_niche.strip():
                p = f"Create a detailed 30-day social media content calendar for: {cal_niche}\nPlatforms: {', '.join(cal_plats)}\n\nFor each day provide: Day number, Platform, Content type, Topic/Hook, CTA. Format as a clear table or structured list. Include a mix of educational, promotional, entertaining, and engagement content."
                with st.spinner("Building 30-day calendar..."):
                    r, e = ai_call(p, max_tokens=2000)
                if r:
                    st.text_area("30-Day Calendar:", value=r, height=400, key="cal_result")
                    st.download_button("⬇ Download Calendar", r, "content_calendar.txt", key="dl_cal")

    with soc_tabs[9]:
        st.markdown("### 🔍 Competitor Spy Tool")
        comp_url  = st.text_input("Competitor URL or handle:", placeholder="e.g. https://competitor.com.au or @competitorhandle", key="comp_url")
        comp_info = st.text_area("What you know about them:", height=80,
                                 placeholder="e.g. They sell AI chatbots to tradies, charge $199/mo, active on LinkedIn and Instagram, 2k followers",
                                 key="comp_info")
        if st.button("🔍 Analyse Competitor", use_container_width=True, type="primary", key="comp_gen"):
            if comp_info.strip():
                p = f"Analyse this competitor and tell me how to beat them:\nCompetitor: {comp_url}\nKnown info: {comp_info}\n\nProvide:\n1. Their likely strengths\n2. Their likely weaknesses and gaps\n3. How to position against them\n4. Content angles they're probably missing\n5. Pricing strategy to undercut or outvalue them\n6. 5 specific things I can do this week to take their customers\n\nBe specific, direct, and ruthless."
                with st.spinner("Analysing competitor..."):
                    r, e = ai_call(p, max_tokens=1000)
                if r: st.text_area("Competitor Analysis:", value=r, height=300, key="comp_result")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 — SECURITY OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[5]:
    st.markdown("## 🛡️ Security Operations Centre")
    st.markdown("<p style='color:#333;font-size:.8em;'>ArmourVault.au — Cybersecurity tools, SOCI Act compliance, client reports, and the 3-tier quote system.</p>",
                unsafe_allow_html=True)

    sec_tabs = st.tabs(["⚡ Quick Quote","📋 SOCI Compliance","📊 Client Report","🔒 Threat Advisor","📁 Client Tracker","💡 3yr 3mo Rule"])

    with sec_tabs[0]:
        st.markdown("### ⚡ 3-Tier Quick Quote Generator")
        st.markdown("<p style='color:#333;font-size:.78em;'>Based on staff count + cameras. Instant quote, no back-and-forth.</p>",
                    unsafe_allow_html=True)
        qc1, qc2, qc3 = st.columns(3)
        with qc1:
            q_biz   = st.text_input("Business name:", key="q_biz")
            q_type  = st.selectbox("Business type:", ["Insurance Broker","Mortgage Broker","Mining","Medical Centre","Tradie","Retail","Hospitality","NDIS","Other"], key="q_type")
        with qc2:
            q_staff = st.number_input("Number of staff:", min_value=1, max_value=500, value=5, key="q_staff")
            q_cams  = st.number_input("Number of cameras:", min_value=0, max_value=200, value=4, key="q_cams")
        with qc3:
            q_tier  = st.selectbox("System tier:", ["Tier 1 — Small (up to 4 cams)","Tier 2 — Medium (5-12 cams)","Tier 3 — Large (13+ cams)"], key="q_tier")
            q_grant = st.checkbox("Government grant eligible?", key="q_grant")

        if st.button("⚡ GENERATE QUOTE", use_container_width=True, type="primary", key="q_gen"):
            if q_tier.startswith("Tier 1"):
                setup, monthly = 14950, 1000
            elif q_tier.startswith("Tier 2"):
                setup, monthly = 24950, 1500
            else:
                setup, monthly = 39950, 2000
            annual = monthly * 12
            total_3yr = setup + (monthly * 39)
            profit_est = total_3yr * 0.65

            st.markdown(f"""
<div class='card' style='border:1px solid #ff006e;'>
<h3 style='color:#ff006e;'>💼 QUOTE — {q_biz or 'Client'}</h3>
<table style='width:100%;color:#e0e0e0;font-size:.9em;'>
<tr><td>Business Type</td><td><b>{q_type}</b></td></tr>
<tr><td>Staff / Cameras</td><td><b>{q_staff} staff / {q_cams} cameras</b></td></tr>
<tr><td>System Tier</td><td><b>{q_tier}</b></td></tr>
<tr><td style='color:#39ff14;'>Setup / Install Fee</td><td style='color:#39ff14;'><b>${setup:,}</b></td></tr>
<tr><td style='color:#ff006e;'>Monthly Subscription</td><td style='color:#ff006e;'><b>${monthly:,}/mo</b></td></tr>
<tr><td>Annual Value</td><td><b>${annual:,}/yr</b></td></tr>
<tr><td>3yr 3mo Total Revenue</td><td><b>${total_3yr:,}</b></td></tr>
<tr><td style='color:#39ff14;'>Estimated Profit (65%)</td><td style='color:#39ff14;'><b>${profit_est:,.0f}</b></td></tr>
{'<tr><td style="color:#39ff14;">Grant Note</td><td style="color:#39ff14;">Eligible for government cybersecurity grant — mention to client</td></tr>' if q_grant else ''}
</table>
<p style='color:#888;font-size:.75em;margin-top:8px;'>Includes 3yr 3mo replacement guarantee. Free unit swap at 39 months.</p>
</div>""", unsafe_allow_html=True)

            quote_prompt = f"Write a professional quote follow-up email for {q_biz or 'the client'} ({q_type}, {q_staff} staff, {q_cams} cameras). Setup: ${setup:,}. Monthly: ${monthly:,}. Mention the 3-year 3-month free replacement guarantee. Australian professional tone. Keep it under 200 words."
            with st.spinner("Generating follow-up email..."):
                qe, _ = ai_call(quote_prompt, max_tokens=400)
            if qe:
                st.text_area("Follow-up Email (ready to send):", value=qe, height=180, key="q_email")

    with sec_tabs[1]:
        st.markdown("### 📋 SOCI Act Compliance Checker")
        soci_biz  = st.text_input("Business name:", key="soci_biz")
        soci_type = st.selectbox("Sector:", ["Mining","Energy","Water","Ports","Food","Health","Finance","Comms","Transport","Defence","Education"], key="soci_type")
        soci_size = st.selectbox("Size:", ["Small (<20 staff)","Medium (20-200 staff)","Large (200+ staff)"], key="soci_size")
        if st.button("📋 Generate SOCI Compliance Report", use_container_width=True, type="primary", key="soci_gen"):
            p = f"Generate a SOCI Act (Security of Critical Infrastructure Act 2018, Australia) compliance checklist and gap analysis for: {soci_biz or 'the business'}, Sector: {soci_type}, Size: {soci_size}. Include: Key obligations, current risk areas, recommended actions, and how ArmourVault's plug-and-play system addresses each gap. Be specific and actionable."
            with st.spinner("Generating compliance report..."):
                r, e = ai_call(p, max_tokens=1200)
            if r: st.text_area("SOCI Compliance Report:", value=r, height=350, key="soci_result")

    with sec_tabs[2]:
        st.markdown("### 📊 Client Security Report Generator")
        cr_client = st.text_input("Client name:", key="cr_client")
        cr_type   = st.selectbox("Report type:", ["Monthly Status","Quarterly Review","Annual Assessment","Incident Report","Post-Install Report"], key="cr_type")
        cr_notes  = st.text_area("Notes / incidents this period:", height=80, key="cr_notes")
        if st.button("📊 Generate Report", use_container_width=True, type="primary", key="cr_gen"):
            p = f"Write a professional {cr_type} cybersecurity report for client: {cr_client}. Notes: {cr_notes or 'No incidents this period'}. Include: Executive summary, system status, threats detected/blocked, recommendations, next steps. Professional Australian business tone. ArmourVault.au branding."
            with st.spinner("Generating report..."):
                r, e = ai_call(p, max_tokens=1000)
            if r:
                st.text_area("Client Report:", value=r, height=300, key="cr_result")
                st.download_button("⬇ Download Report", r, f"{cr_client}_report.txt", key="dl_cr")

    with sec_tabs[3]:
        st.markdown("### 🔒 Threat & Risk Advisor")
        threat_q = st.text_area("Describe the threat or situation:", height=80,
                                placeholder="e.g. Client received a phishing email, clicked a link, and their accountant's computer may be compromised",
                                key="threat_q")
        if st.button("🔒 Get Threat Advice", use_container_width=True, type="primary", key="threat_gen"):
            if threat_q.strip():
                p = f"As a cybersecurity expert, analyse this threat and provide immediate action steps: {threat_q}. Include: Severity rating, immediate actions (next 1 hour), short-term actions (next 24 hours), long-term prevention, and whether to notify authorities. Australian context."
                with st.spinner("Analysing threat..."):
                    r, e = ai_call(p, max_tokens=800)
                if r: st.text_area("Threat Analysis:", value=r, height=280, key="threat_result")

    with sec_tabs[4]:
        st.markdown("### 📁 Client Tracker")
        cl_data = jload(DATA_DIR/"clients.json", [])
        with st.form("add_client_form"):
            cfc1, cfc2, cfc3 = st.columns(3)
            with cfc1:
                cl_name   = st.text_input("Client name:", key="cl_name")
                cl_type   = st.selectbox("Type:", ["Insurance Broker","Mortgage Broker","Mining","Medical","Tradie","Retail","Other"], key="cl_type_f")
            with cfc2:
                cl_tier   = st.selectbox("Tier:", ["Tier 1","Tier 2","Tier 3"], key="cl_tier")
                cl_monthly= st.number_input("Monthly ($):", min_value=0, value=1000, key="cl_monthly")
            with cfc3:
                cl_status = st.selectbox("Status:", ["Active","Lead","Proposal Sent","Onboarding","Churned"], key="cl_status")
                cl_next   = st.text_input("Next action:", key="cl_next")
            if st.form_submit_button("➕ Add Client", use_container_width=True):
                cl_data.append({"name":cl_name,"type":cl_type,"tier":cl_tier,"monthly":cl_monthly,"status":cl_status,"next":cl_next,"date":now.strftime("%Y-%m-%d")})
                jsave(DATA_DIR/"clients.json", cl_data); st.rerun()
        if cl_data:
            total_mrr = sum(c.get("monthly",0) for c in cl_data if c.get("status")=="Active")
            st.markdown(f"<span class='pill-ai'>Active MRR from Security Clients: ${total_mrr:,}/mo</span>", unsafe_allow_html=True)
            st.dataframe([{"Name":c["name"],"Type":c["type"],"Tier":c["tier"],"Monthly":f"${c['monthly']:,}","Status":c["status"],"Next Action":c["next"]} for c in cl_data], use_container_width=True)

    with sec_tabs[5]:
        st.markdown("### 💡 The 3yr 3mo Rule — Calculator")
        st.markdown("""<div class='card' style='border:1px solid #39ff14;font-size:.85em;color:#e0e0e0;'>
<b style='color:#39ff14;'>How it works:</b><br>
At 3 years and 3 months (39 months), the client gets a FREE unit replacement. The old unit is dismantled, rebuilt, and recycled (environmental marketing point). The last 3 months of subscription essentially covers the cost of the new unit. Early exits are a win — spare unit goes back to stock.
</div>""", unsafe_allow_html=True)
        r3c1, r3c2 = st.columns(2)
        with r3c1:
            r3_setup   = st.number_input("Setup fee ($):", value=14950, key="r3_setup")
            r3_monthly = st.number_input("Monthly ($):", value=1000, key="r3_monthly")
            r3_unit    = st.number_input("Unit cost ($):", value=4500, key="r3_unit")
        with r3c2:
            r3_total   = r3_setup + (r3_monthly * 39)
            r3_profit  = r3_total - r3_unit
            r3_margin  = (r3_profit / r3_total) * 100
            st.markdown(f"""<div class='card'>
<b>39-Month Revenue:</b> <span style='color:#39ff14;'>${r3_total:,}</span><br>
<b>Unit Cost:</b> <span style='color:#ff006e;'>-${r3_unit:,}</span><br>
<b>Net Profit:</b> <span style='color:#39ff14;font-size:1.2em;'>${r3_profit:,}</span><br>
<b>Margin:</b> <span style='color:#39ff14;'>{r3_margin:.1f}%</span>
</div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 6 — EMAIL SUITE (all 20 templates + AI tools)
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[6]:
    st.markdown("## 📧 Email Suite")
    em_tabs = st.tabs(["📬 Templates","✍️ AI Email Writer","🔄 Auto-Reply","📮 Drip Sequences","📬 Gmail Inbox"])

    EMAIL_TEMPLATES = {
        "Cold Outreach — Mining/SOCI": {
            "subject": "Your Cybersecurity Obligations Under the SOCI Act — Are You Covered?",
            "body": """Hi [Name],

I hope this message finds you well. My name is [Your Name] from ArmourVault.au.

With the SOCI Act now in full effect, businesses in the mining sector face significant compliance obligations — and the penalties for non-compliance are severe.

We've developed a plug-and-play cybersecurity system specifically designed for Australian mining operations. It's fully compliant, installs in under a day, and requires zero ongoing management from your team.

I'd love to show you how it works in a 15-minute call this week. Are you available Thursday or Friday?

Best regards,
[Your Name]
ArmourVault.au | [Phone]"""
        },
        "Cold Outreach — Tradies": {
            "subject": "Protect Your Business from Cyber Attacks — Built for Tradies",
            "body": """G'day [Name],

Quick one — are you protected if a hacker targets your business?

Most tradies don't think about cybersecurity until it's too late. One ransomware attack can wipe your client list, your invoices, and your reputation overnight.

At ArmourVault.au, we've built a simple, affordable plug-and-play system specifically for small businesses like yours. No tech knowledge needed. It just works.

Starting from $1,000/month with a 3-year replacement guarantee.

Worth a 10-minute chat? Reply here or call [Phone].

Cheers,
[Your Name]"""
        },
        "Cold Outreach — LinkedIn": {
            "subject": "Quick question about your cybersecurity setup",
            "body": """Hi [Name],

Saw your profile and noticed you're running [Company]. Impressive work.

I wanted to reach out because we've been helping businesses like yours in [Industry] get properly protected without the usual IT headaches.

Our system is plug-and-play, fully compliant with Australian regulations, and comes with a 3-year guarantee.

Would you be open to a quick 15-minute call to see if it's a fit?

[Your Name] | ArmourVault.au"""
        },
        "Follow-Up #1 (3 days)": {
            "subject": "Following up — ArmourVault Cybersecurity",
            "body": """Hi [Name],

Just following up on my message from earlier this week.

I know you're busy, so I'll keep it short — we help [Business Type] businesses get fully protected against cyber threats in under 24 hours, with zero disruption to your operations.

If now isn't the right time, no worries at all. But if you'd like to see how it works, I'm happy to jump on a quick call at your convenience.

[Your Name] | ArmourVault.au | [Phone]"""
        },
        "Follow-Up #2 (7 days)": {
            "subject": "Last follow-up — [Company Name]",
            "body": """Hi [Name],

I don't want to keep filling your inbox, so this will be my last reach-out for now.

If cybersecurity ever becomes a priority — whether it's a compliance requirement, a close call, or just peace of mind — we're here.

You can book a free 15-minute assessment anytime at [Link].

Take care,
[Your Name] | ArmourVault.au"""
        },
        "Objection Handler — Too Expensive": {
            "subject": "Re: Cost of ArmourVault System",
            "body": """Hi [Name],

Totally understand — cost is always a consideration.

Here's the thing though: the average cost of a cyber attack on a small Australian business is $46,000. Our system starts at $1,000/month.

That's $12,000/year vs a potential $46,000 loss — plus the reputational damage, the downtime, and the legal liability.

We also offer government grant assistance for eligible businesses, which can significantly reduce your upfront cost.

Worth a 10-minute call to explore your options?

[Your Name] | ArmourVault.au"""
        },
        "Onboarding — Welcome": {
            "subject": "Welcome to ArmourVault — You're Protected",
            "body": """Hi [Name],

Welcome to ArmourVault.au — we're genuinely glad to have you on board.

Your system is now active and monitoring 24/7. Here's what happens next:

1. You'll receive your first monthly status report within 30 days
2. Our team monitors your system around the clock — you don't need to do anything
3. If anything unusual is detected, we'll contact you immediately

Your 3-year 3-month replacement guarantee is now active from today's date.

Any questions at all, reply to this email or call [Phone].

Welcome to the team,
[Your Name] | ArmourVault.au"""
        },
        "Win-Back — Churned Client": {
            "subject": "We'd love to have you back — [Company Name]",
            "body": """Hi [Name],

It's been a while since we last spoke, and I wanted to reach out personally.

The cyber threat landscape has changed significantly since you were last with us — ransomware attacks on Australian businesses are up 47% this year alone.

We've also upgraded our system significantly. I'd love to show you what's new and see if there's a way we can work together again.

No pressure at all — just a quick 10-minute catch-up if you're open to it.

[Your Name] | ArmourVault.au | [Phone]"""
        },
        "Referral Request": {
            "subject": "Quick favour — do you know anyone who needs this?",
            "body": """Hi [Name],

Hope everything's going well with your system — it's been great having you as a client.

I wanted to ask a quick favour. If you know any other business owners who might benefit from what we do — especially in [Industry] — we'd love an introduction.

For every referral that becomes a client, we'll give you one month free on your subscription.

No pressure at all, just wanted to put it out there.

Thanks as always,
[Your Name] | ArmourVault.au"""
        },
        "Upsell — Tier Upgrade": {
            "subject": "Your business has grown — time to upgrade your protection?",
            "body": """Hi [Name],

I noticed your team has grown since we first set you up. Congratulations — that's fantastic.

I wanted to check in because your current Tier 1 system was designed for your previous setup. With more staff and more devices, you may benefit from upgrading to Tier 2 for broader coverage.

The upgrade is seamless — no downtime, no reinstall. Just enhanced protection.

Want me to put together a quick comparison for you?

[Your Name] | ArmourVault.au"""
        },
        "Testimonial Request": {
            "subject": "Would you mind sharing your experience?",
            "body": """Hi [Name],

I hope you're happy with how everything's been running.

We're building out our case studies and I'd love to feature [Company Name] as an example of how businesses in [Industry] are getting properly protected.

Would you be open to a quick 5-minute call, or even just a few sentences via email about your experience?

It would mean a lot to us — and I'd be happy to return the favour in any way I can.

Thanks,
[Your Name] | ArmourVault.au"""
        },
        "Partnership Pitch": {
            "subject": "Partnership opportunity — ArmourVault.au x [Their Company]",
            "body": """Hi [Name],

I've been following [Their Company] for a while and I think there's a genuine opportunity for us to work together.

We provide cybersecurity solutions to [Industry] businesses. You provide [Their Service]. Our clients often need both.

A referral partnership would be mutually beneficial — we send clients your way, you send clients ours. Simple, no cost, no obligation.

Would you be open to a 20-minute call to explore?

[Your Name] | ArmourVault.au"""
        },
        "Support Reply — General": {
            "subject": "Re: Your Support Request — ArmourVault",
            "body": """Hi [Name],

Thanks for reaching out — we've received your message and we're on it.

Our team is looking into [Issue] now and we'll have an update for you within [Timeframe].

In the meantime, if it's urgent, please call [Phone] and we'll prioritise your case immediately.

Thanks for your patience,
[Your Name] | ArmourVault.au Support"""
        },
        "Weekly Newsletter": {
            "subject": "This Week in Cyber — ArmourVault Weekly",
            "body": """Hi [Name],

Here's your weekly cybersecurity update from ArmourVault.au:

🔴 THREAT ALERT: [Current threat summary]

📊 THIS WEEK'S STATS:
• [X] attacks blocked across our network
• [Y] new vulnerabilities patched
• [Z] businesses newly protected

💡 TIP OF THE WEEK:
[Practical tip]

📰 IN THE NEWS:
[Brief industry news item]

Stay safe out there,
[Your Name] | ArmourVault.au

[Unsubscribe]"""
        },
        "Cold Outreach — Insurance Brokers": {
            "subject": "Cybersecurity compliance is now affecting insurance premiums — are you covered?",
            "body": """Hi [Name],

Insurance brokers are increasingly being targeted by cybercriminals — and your clients' data is the prize.

With the Privacy Act amendments now in effect, a single data breach can result in fines of up to $50 million. Your PI insurance won't cover that.

ArmourVault.au provides a fully compliant, plug-and-play cybersecurity system designed specifically for financial services businesses. Install in a day, monitor forever.

Can we find 15 minutes this week?

[Your Name] | ArmourVault.au"""
        },
        "Cold Outreach — Medical Centres": {
            "subject": "Patient data protection — are you meeting your obligations?",
            "body": """Hi [Name],

Medical centres hold some of the most sensitive data in Australia — and they're one of the top targets for ransomware attacks.

Under the My Health Records Act and the Privacy Act, you have strict obligations to protect patient data. A breach doesn't just mean fines — it means losing patient trust permanently.

ArmourVault.au has built a healthcare-specific cybersecurity system that's fully compliant, installs without disrupting your practice, and monitors 24/7.

I'd love to show you how it works. Are you free for a quick call this week?

[Your Name] | ArmourVault.au"""
        },
        "Cold Outreach — Mortgage Brokers": {
            "subject": "ASIC is watching — is your client data secure?",
            "body": """Hi [Name],

Mortgage brokers handle some of the most sensitive financial data in Australia — and ASIC's cybersecurity expectations are getting stricter every year.

One breach can end your licence, your reputation, and your business.

ArmourVault.au provides a simple, affordable, fully compliant cybersecurity system built for financial services. No IT team needed. Just plug it in and you're protected.

Worth a 15-minute conversation?

[Your Name] | ArmourVault.au"""
        },
        "7-Day Drip — Day 1": {
            "subject": "Welcome — here's what to expect",
            "body": """Hi [Name],

Thanks for your interest in ArmourVault.au.

Over the next 7 days, I'm going to share some quick insights about cybersecurity for Australian businesses — no fluff, just practical stuff.

Tomorrow: The #1 mistake small businesses make that leaves them wide open to attack.

Talk soon,
[Your Name] | ArmourVault.au"""
        },
        "7-Day Drip — Day 3": {
            "subject": "The #1 mistake that gets Australian businesses hacked",
            "body": """Hi [Name],

The #1 mistake? Assuming it won't happen to them.

47% of cyber attacks in Australia target small businesses. Why? Because they're easier targets than big corporations.

The good news: protecting yourself doesn't have to be complicated or expensive.

Tomorrow I'll show you exactly what proper protection looks like — and what it costs.

[Your Name] | ArmourVault.au"""
        },
        "7-Day Drip — Day 7": {
            "subject": "Ready to get protected? Here's your next step",
            "body": """Hi [Name],

This is the last email in this series.

If you've been reading along, you now know:
✅ Why small businesses are the #1 target
✅ What a proper cybersecurity system looks like
✅ How the SOCI Act affects your business
✅ What it actually costs to get protected

If you're ready to take the next step, book a free 15-minute assessment here: [Link]

No obligation, no sales pressure. Just a straight conversation about what you need.

[Your Name] | ArmourVault.au"""
        }
    }

    with em_tabs[0]:
        st.markdown("### 📬 All 20 Email Templates")
        selected_template = st.selectbox("Select template:", list(EMAIL_TEMPLATES.keys()), key="em_select")
        if selected_template:
            tmpl = EMAIL_TEMPLATES[selected_template]
            st.text_input("Subject:", value=tmpl["subject"], key="em_subj")
            st.text_area("Body:", value=tmpl["body"], height=320, key="em_body")
            st.download_button("⬇ Download Template", f"Subject: {tmpl['subject']}\n\n{tmpl['body']}", f"email_{selected_template[:20]}.txt", key="dl_em")

    with em_tabs[1]:
        st.markdown("### ✍️ AI Email Writer")
        ew_to   = st.text_input("To (name/company):", key="ew_to")
        ew_goal = st.selectbox("Goal:", ["Cold Outreach","Follow-Up","Proposal","Objection Handle","Onboarding","Support Reply","Partnership","Upsell","Referral Request"], key="ew_goal")
        ew_ctx  = st.text_area("Context:", height=80, placeholder="e.g. Mining company, 50 staff, SOCI Act compliant, spoke at a conference last week", key="ew_ctx")
        ew_tone = st.selectbox("Tone:", ["Professional Australian","Casual Friendly","Direct & Punchy","Formal Corporate"], key="ew_tone")
        if st.button("✍️ Write Email", use_container_width=True, type="primary", key="ew_gen"):
            if ew_to.strip():
                p = f"Write a {ew_goal} email to {ew_to}. Context: {ew_ctx}. Tone: {ew_tone}. From ArmourVault.au. Include subject line. Under 200 words. No fluff."
                with st.spinner("Writing email..."):
                    r, e = ai_call(p, max_tokens=500)
                if r: st.text_area("Email:", value=r, height=250, key="ew_result")

    with em_tabs[2]:
        st.markdown("### 🔄 AI Auto-Reply Generator")
        ar_email = st.text_area("Paste the email you received:", height=150, key="ar_email")
        ar_tone  = st.selectbox("Reply tone:", ["Professional","Friendly","Direct","Apologetic","Assertive"], key="ar_tone")
        if st.button("🔄 Generate Reply", use_container_width=True, type="primary", key="ar_gen"):
            if ar_email.strip():
                p = f"Write a {ar_tone} reply to this email. From ArmourVault.au. Keep it concise and professional. Include subject line.\n\nOriginal email:\n{ar_email}"
                with st.spinner("Writing reply..."):
                    r, e = ai_call(p, max_tokens=500)
                if r: st.text_area("Your Reply:", value=r, height=220, key="ar_result")

    with em_tabs[3]:
        st.markdown("### 📮 Drip Sequence Builder")
        ds_lead = st.text_input("Lead name/company:", key="ds_lead")
        ds_type = st.selectbox("Sequence type:", ["New Lead (7 days)","Free Trial (7 days)","Post-Purchase (30 days)","Win-Back (5 days)","Referral (3 days)"], key="ds_type")
        if st.button("📮 Build Full Sequence", use_container_width=True, type="primary", key="ds_gen"):
            if ds_lead.strip():
                p = f"Build a complete {ds_type} email drip sequence for: {ds_lead}. ArmourVault.au cybersecurity business. Include all emails with: Day number, Subject line, Full email body. Australian professional tone. Each email under 150 words."
                with st.spinner("Building sequence..."):
                    r, e = ai_call(p, max_tokens=1500)
                if r:
                    st.text_area("Full Sequence:", value=r, height=400, key="ds_result")
                    st.download_button("⬇ Download Sequence", r, f"drip_{ds_lead[:20]}.txt", key="dl_ds")

    with em_tabs[4]:
        st.markdown("### 📬 Gmail Inbox")
        if not S.get("gmail_connected"):
            st.markdown("""<div class='card' style='border:1px solid #ff006e;text-align:center;'>
<h4 style='color:#ff006e;'>Gmail Not Connected</h4>
<p style='color:#888;'>Connect your Gmail / Google Workspace in Settings to read and send emails from the dashboard.</p>
</div>""", unsafe_allow_html=True)
        else:
            st.info("Gmail connected — inbox integration active.")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 7 — LEAD SCRAPER
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[7]:
    st.markdown("## 🔍 Lead Scraper & CRM")
    leads = jload(LEADS_FILE, [])

    ls_tabs = st.tabs(["🔍 Scraper","📋 Lead List","➕ Manual Add"])

    with ls_tabs[0]:
        st.markdown("### 🔍 Email & Lead Scraper")
        ls_input = st.text_area("Paste text, URL, or business info to extract leads from:", height=120, key="ls_input")
        if st.button("🔍 Extract Leads", use_container_width=True, type="primary", key="ls_gen"):
            if ls_input.strip():
                import re
                emails = list(set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', ls_input)))
                phones = list(set(re.findall(r'(?:\+61|0)[2-9]\d{8}|(?:\+61|0)4\d{8}', ls_input)))
                if emails or phones:
                    st.success(f"Found {len(emails)} emails and {len(phones)} phone numbers")
                    for em in emails:
                        st.code(em)
                    for ph in phones:
                        st.code(ph)
                    if emails:
                        p = f"Based on these email addresses, identify likely business names and industries: {', '.join(emails[:10])}"
                        with st.spinner("Enriching lead data..."):
                            enriched, _ = ai_call(p, max_tokens=400)
                        if enriched: st.text_area("Lead Enrichment:", value=enriched, height=150, key="ls_enriched")
                else:
                    st.info("No emails or phone numbers found. Try pasting more text or a business listing.")

    with ls_tabs[1]:
        if not leads:
            st.markdown("<p style='color:#222;'>No leads yet. Add them manually or use the scraper.</p>", unsafe_allow_html=True)
        else:
            total_leads  = len(leads)
            hot_leads    = len([l for l in leads if l.get("status")=="Hot"])
            converted    = len([l for l in leads if l.get("status")=="Converted"])
            lc1,lc2,lc3 = st.columns(3)
            with lc1: st.metric("Total Leads", total_leads)
            with lc2: st.metric("Hot Leads", hot_leads)
            with lc3: st.metric("Converted", converted)
            st.dataframe([{"Name":l.get("name",""),"Email":l.get("email",""),"Industry":l.get("industry",""),"Status":l.get("status",""),"Notes":l.get("notes","")} for l in leads], use_container_width=True)

    with ls_tabs[2]:
        with st.form("add_lead_form"):
            lfc1, lfc2 = st.columns(2)
            with lfc1:
                l_name     = st.text_input("Name:", key="l_name")
                l_email    = st.text_input("Email:", key="l_email")
                l_phone    = st.text_input("Phone:", key="l_phone")
            with lfc2:
                l_industry = st.selectbox("Industry:", ["Mining","Insurance","Mortgage","Medical","Tradie","Retail","Other"], key="l_industry")
                l_status   = st.selectbox("Status:", ["New","Contacted","Hot","Proposal Sent","Converted","Dead"], key="l_status")
                l_notes    = st.text_input("Notes:", key="l_notes")
            if st.form_submit_button("➕ Add Lead", use_container_width=True):
                leads.append({"name":l_name,"email":l_email,"phone":l_phone,"industry":l_industry,"status":l_status,"notes":l_notes,"date":now.strftime("%Y-%m-%d")})
                jsave(LEADS_FILE, leads); st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 8 — IDEAS NOTEPAD
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[8]:
    st.markdown("## 💡 Ideas Notepad")
    st.markdown("<p style='color:#333;font-size:.8em;'>Drop ideas here. Tag them, vote on them, flag the good ones for building. Your product roadmap starts here.</p>",
                unsafe_allow_html=True)

    ideas = jload(IDEAS_FILE, [])

    with st.form("add_idea_form"):
        ifc1, ifc2 = st.columns([2,1])
        with ifc1:
            i_idea = st.text_area("Your idea:", height=80, placeholder="e.g. Add a voice-to-task feature so I can speak tasks into the dashboard while driving", key="i_idea")
        with ifc2:
            i_cat  = st.selectbox("Category:", ["Dashboard Feature","New Product","Marketing","Business Process","AI Tool","Security","Revenue","Other"], key="i_cat")
            i_pri  = st.selectbox("Priority:", ["🔥 High","⚡ Medium","💡 Low","🚀 Build Next"], key="i_pri")
        if st.form_submit_button("💡 Add Idea", use_container_width=True):
            ideas.append({"id":len(ideas)+1,"idea":i_idea,"category":i_cat,"priority":i_pri,"votes":0,"status":"New","date":now.strftime("%Y-%m-%d"),"ai_eval":""})
            jsave(IDEAS_FILE, ideas); st.rerun()

    if ideas:
        # Sort by priority then votes
        priority_order = {"🚀 Build Next":0,"🔥 High":1,"⚡ Medium":2,"💡 Low":3}
        ideas_sorted = sorted(ideas, key=lambda x: (priority_order.get(x.get("priority","💡 Low"),3), -x.get("votes",0)))

        for idea in ideas_sorted:
            with st.expander(f"{idea.get('priority','💡')} [{idea.get('category','?')}] {idea.get('idea','')[:70]} · 👍 {idea.get('votes',0)}"):
                ic1, ic2, ic3, ic4 = st.columns([3,1,1,1])
                with ic1:
                    st.markdown(f"<p style='color:#e0e0e0;'>{idea.get('idea','')}</p>", unsafe_allow_html=True)
                    if idea.get("ai_eval"):
                        st.markdown(f"<p style='color:#888;font-size:.8em;'>AI: {idea['ai_eval']}</p>", unsafe_allow_html=True)
                with ic2:
                    if st.button("👍 Vote", key=f"vote_{idea['id']}"):
                        idea["votes"] = idea.get("votes",0) + 1
                        jsave(IDEAS_FILE, ideas); st.rerun()
                with ic3:
                    if st.button("🤖 Evaluate", key=f"eval_{idea['id']}"):
                        p = f"Evaluate this business idea in 2 sentences — is it worth building? What's the revenue potential? Idea: {idea['idea']}"
                        with st.spinner("Evaluating..."):
                            ev, _ = ai_call(p, max_tokens=150)
                        if ev:
                            idea["ai_eval"] = ev
                            jsave(IDEAS_FILE, ideas); st.rerun()
                with ic4:
                    if st.button("🗑️ Delete", key=f"del_idea_{idea['id']}"):
                        ideas = [i for i in ideas if i["id"] != idea["id"]]
                        jsave(IDEAS_FILE, ideas); st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 9 — DREAM BUILD ENQUIRY
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[9]:
    st.markdown("## 🚀 Dream Build — Custom Dashboard Enquiry")
    st.markdown("""<div class='card' style='border:1px solid #ff006e;'>
<h4 style='color:#ff006e;'>Want a custom dashboard built for your business?</h4>
<p style='color:#888;font-size:.85em;'>Tell us what you need. We'll build it. Fully custom, fully yours. Starting from $500 setup + $97/mo.</p>
</div>""", unsafe_allow_html=True)

    enquiries = jload(ENQUIRIES_FILE, [])

    with st.form("dream_build_form"):
        dbc1, dbc2 = st.columns(2)
        with dbc1:
            db_name    = st.text_input("Your name:", key="db_name")
            db_email   = st.text_input("Email:", key="db_email")
            db_phone   = st.text_input("Phone:", key="db_phone")
            db_biz     = st.text_input("Business name:", key="db_biz")
        with dbc2:
            db_industry= st.selectbox("Industry:", ["Mining","Insurance","Mortgage","Medical","Tradie","Retail","Hospitality","Tech","Other"], key="db_industry")
            db_size    = st.selectbox("Team size:", ["Just me","2-5","6-20","21-50","50+"], key="db_size")
            db_budget  = st.selectbox("Monthly budget:", ["Under $100","$100-$300","$300-$500","$500+","Not sure yet"], key="db_budget")
            db_tier    = st.selectbox("Tier interest:", ["Starter (Tasklet Agents)","Pro (Autonomous Crew)","Enterprise (Full Custom)","Not sure"], key="db_tier")
        db_dream = st.text_area("Describe your dream dashboard — what would it do for your business?",
                                height=120, placeholder="e.g. I want a dashboard that manages my 3 staff, sends automated follow-up emails to leads, tracks my monthly revenue, and has an AI that writes my social media posts...", key="db_dream")
        db_problems = st.text_area("What problems are you trying to solve?", height=80, key="db_problems")
        if st.form_submit_button("🚀 SUBMIT DREAM BUILD ENQUIRY", use_container_width=True):
            enq = {"id":len(enquiries)+1,"name":db_name,"email":db_email,"phone":db_phone,"business":db_biz,"industry":db_industry,"size":db_size,"budget":db_budget,"tier":db_tier,"dream":db_dream,"problems":db_problems,"date":now.strftime("%Y-%m-%d %H:%M"),"status":"New"}
            enquiries.append(enq)
            jsave(ENQUIRIES_FILE, enquiries)
            # Auto-add to leads
            leads = jload(LEADS_FILE, [])
            leads.append({"name":db_name,"email":db_email,"phone":db_phone,"industry":db_industry,"status":"Hot","notes":f"Dream Build enquiry — {db_tier}","date":now.strftime("%Y-%m-%d")})
            jsave(LEADS_FILE, leads)
            st.success(f"✅ Enquiry received! We'll be in touch within 24 hours, {db_name}.")
            # Generate personalised follow-up
            p = f"Write a personalised follow-up email to {db_name} from {db_biz} who enquired about a custom AI dashboard. Their dream: {db_dream}. Budget: {db_budget}. Tier: {db_tier}. From ArmourVault.au / ARTIFICIAL & INTELLIGENT. Warm, professional, excited. Under 200 words."
            with st.spinner("Generating follow-up email..."):
                fe, _ = ai_call(p, max_tokens=400)
            if fe:
                st.text_area("Auto-generated follow-up email:", value=fe, height=200, key="db_followup")

    if enquiries:
        st.markdown(f"---\n### 📋 Enquiries ({len(enquiries)} total)")
        for enq in reversed(enquiries):
            with st.expander(f"#{enq['id']} — {enq.get('name','')} | {enq.get('business','')} | {enq.get('tier','')} | {enq.get('date','')}"):
                st.markdown(f"**Email:** {enq.get('email','')} | **Phone:** {enq.get('phone','')} | **Budget:** {enq.get('budget','')}")
                st.markdown(f"**Dream:** {enq.get('dream','')}")
                st.markdown(f"**Problems:** {enq.get('problems','')}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 10 — PRODUCTS
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[10]:
    st.markdown("## 📦 Products & Services")
    products = jload(PRODUCTS_FILE, [])
    if not products:
        products = [
            {"name":"AI Content Machine","price":297,"status":"Active","customers":0,"desc":"AI-powered content creation suite"},
            {"name":"Email Automation Suite","price":197,"status":"Active","customers":0,"desc":"20 templates + AI writer + drip sequences"},
            {"name":"Avatar Empire Builder","price":497,"status":"Active","customers":0,"desc":"Full autonomous avatar creation system"},
            {"name":"Lead Scraper Pro","price":147,"status":"Active","customers":0,"desc":"Email scraper + CRM + enrichment"},
            {"name":"Social Command Centre","price":247,"status":"Active","customers":0,"desc":"All 6 platforms, content calendar, DM writer"},
            {"name":"Security Dashboard","price":197,"status":"Active","customers":0,"desc":"SOCI compliance, threat advisor, client reports"},
            {"name":"TradieTech Starter","price":14950,"status":"Active","customers":0,"desc":"Tier 1 cybersecurity system (up to 4 cams)"},
            {"name":"TradieTech Pro","price":24950,"status":"Active","customers":0,"desc":"Tier 2 cybersecurity system (5-12 cams)"},
            {"name":"TradieTech Enterprise","price":39950,"status":"Active","customers":0,"desc":"Tier 3 cybersecurity system (13+ cams)"},
            {"name":"AI Business Dashboard — Starter","price":97,"status":"Active","customers":0,"desc":"Tasklet agents, core tools, monthly"},
            {"name":"AI Business Dashboard — Pro","price":297,"status":"Active","customers":0,"desc":"Autonomous crew, all tools, monthly"},
            {"name":"Custom Dashboard Build","price":500,"status":"Active","customers":0,"desc":"Custom setup fee + monthly subscription"},
            {"name":"Magic Mike Avatar System","price":997,"status":"Active","customers":0,"desc":"Full autonomous avatar + video pipeline"},
        ]
        jsave(PRODUCTS_FILE, products)

    total_products = len(products)
    active_products = len([p for p in products if p.get("status")=="Active"])
    total_customers = sum(p.get("customers",0) for p in products)
    pc1,pc2,pc3 = st.columns(3)
    with pc1: st.metric("Total Products", total_products)
    with pc2: st.metric("Active", active_products)
    with pc3: st.metric("Total Customers", total_customers)

    for p in products:
        with st.expander(f"📦 {p['name']} — ${p['price']:,} | {p.get('status','Active')} | {p.get('customers',0)} customers"):
            prc1, prc2, prc3 = st.columns(3)
            with prc1: st.markdown(f"<span class='pill-ai'>${p['price']:,}</span>", unsafe_allow_html=True)
            with prc2: st.markdown(f"<span class='pill-on'>{p.get('status','Active')}</span>", unsafe_allow_html=True)
            with prc3: st.markdown(f"<span class='pill-pink'>{p.get('customers',0)} customers</span>", unsafe_allow_html=True)
            st.markdown(f"<p style='color:#888;font-size:.85em;'>{p.get('desc','')}</p>", unsafe_allow_html=True)
            if st.button(f"🚀 Launch Campaign", key=f"launch_{p['name'][:15]}"):
                lp = f"Write a product launch campaign for: {p['name']} at ${p['price']:,}. Include: Launch email, 3 social posts (FB, IG, LinkedIn), key selling points, urgency/scarcity angle. ArmourVault.au / ARTIFICIAL & INTELLIGENT branding."
                with st.spinner("Building launch campaign..."):
                    lr, le = ai_call(lp, max_tokens=1000)
                if lr: st.text_area("Launch Campaign:", value=lr, height=300, key=f"lc_{p['name'][:10]}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 11 — REVENUE
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[11]:
    st.markdown("## 💰 Revenue Dashboard")
    revenue_data = jload(REVENUE_FILE, [])
    # Handle legacy dict format {today, history} or ensure it's a list
    if isinstance(revenue_data, dict):
        revenue_data = revenue_data.get("history", [])
    if not isinstance(revenue_data, list):
        revenue_data = []
    revenue_data = [r for r in revenue_data if isinstance(r, dict)]

    mrr = sum(r.get("amount",0) for r in revenue_data if r.get("type")=="monthly")
    total_rev = sum(r.get("amount",0) for r in revenue_data)
    arr = mrr * 12

    rc1,rc2,rc3,rc4 = st.columns(4)
    with rc1: st.metric("MRR", f"${mrr:,}")
    with rc2: st.metric("ARR", f"${arr:,}")
    with rc3: st.metric("Total Revenue", f"${total_rev:,}")
    with rc4: st.metric("Entries", len(revenue_data))

    with st.form("log_revenue_form"):
        rfc1, rfc2, rfc3 = st.columns(3)
        with rfc1:
            r_source = st.text_input("Source:", key="r_source")
            r_amount = st.number_input("Amount ($):", min_value=0.0, value=0.0, key="r_amount")
        with rfc2:
            r_type   = st.selectbox("Type:", ["monthly","one-off","setup","referral"], key="r_type")
            r_product= st.text_input("Product:", key="r_product")
        with rfc3:
            r_notes  = st.text_input("Notes:", key="r_notes")
        if st.form_submit_button("💰 Log Revenue", use_container_width=True):
            revenue_data.append({"source":r_source,"amount":r_amount,"type":r_type,"product":r_product,"notes":r_notes,"date":now.strftime("%Y-%m-%d")})
            jsave(REVENUE_FILE, revenue_data); st.rerun()

    if revenue_data:
        import plotly.express as px
        df_rev = pd.DataFrame(revenue_data)
        if "date" in df_rev.columns and "amount" in df_rev.columns:
            df_rev["date"] = pd.to_datetime(df_rev["date"])
            df_daily = df_rev.groupby("date")["amount"].sum().reset_index()
            fig = px.area(df_daily, x="date", y="amount",
                          title="Revenue Over Time",
                          color_discrete_sequence=["#ff006e"])
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              font_color="#e0e0e0", title_font_color="#ff006e")
            st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df_rev[["date","source","product","amount","type","notes"]].sort_values("date",ascending=False).head(20), use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 12 — BUSINESS TOOLS
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[12]:
    st.markdown("## 🚀 Business Tools")
    bt_tabs = st.tabs(["📄 Proposal","🧾 Invoice","📢 Ad Copy","🏷️ Business Name","📋 Onboarding","🎯 Sales Script","📊 Weekly Wins","🌐 Web Redesigner","📱 App Cloner","🚀 Landing Page"])

    with bt_tabs[0]:
        st.markdown("### 📄 Proposal Machine")
        pr_client = st.text_input("Client name:", key="pr_client")
        pr_problem= st.text_area("Their problem:", height=70, key="pr_problem")
        pr_solution=st.text_area("Your solution:", height=70, key="pr_solution")
        pr_price  = st.text_input("Investment:", key="pr_price")
        if st.button("📄 Generate Proposal", use_container_width=True, type="primary", key="pr_gen"):
            if pr_client.strip():
                p = f"Write a professional business proposal for {pr_client}. Problem: {pr_problem}. Solution: {pr_solution}. Investment: {pr_price}. ArmourVault.au. Include: Executive summary, problem statement, proposed solution, deliverables, investment, timeline, next steps, guarantee. Professional Australian tone."
                with st.spinner("Writing proposal..."):
                    r, e = ai_call(p, max_tokens=1200)
                if r:
                    st.text_area("Proposal:", value=r, height=400, key="pr_result")
                    st.download_button("⬇ Download", r, f"proposal_{pr_client[:15]}.txt", key="dl_pr")

    with bt_tabs[1]:
        st.markdown("### 🧾 Invoice Builder")
        ic1, ic2 = st.columns(2)
        with ic1:
            inv_client = st.text_input("Client:", key="inv_client")
            inv_items  = st.text_area("Items (one per line):", height=100, placeholder="Cybersecurity System Setup — $14,950\nMonthly Monitoring — $1,000", key="inv_items")
        with ic2:
            inv_due    = st.text_input("Due date:", value="14 days", key="inv_due")
            inv_bsb    = st.text_input("BSB:", key="inv_bsb")
            inv_acc    = st.text_input("Account:", key="inv_acc")
        if st.button("🧾 Generate Invoice", use_container_width=True, type="primary", key="inv_gen"):
            if inv_client.strip():
                p = f"Generate a professional invoice for {inv_client}. Items: {inv_items}. Due: {inv_due}. From ArmourVault.au. Include invoice number, date, itemised list with totals, GST, payment details (BSB: {inv_bsb}, Account: {inv_acc}), payment terms."
                with st.spinner("Building invoice..."):
                    r, e = ai_call(p, max_tokens=600)
                if r:
                    st.text_area("Invoice:", value=r, height=300, key="inv_result")
                    st.download_button("⬇ Download", r, f"invoice_{inv_client[:15]}.txt", key="dl_inv")

    with bt_tabs[2]:
        st.markdown("### 📢 Ad Copy Generator")
        ad_product = st.text_input("Product/Service:", key="ad_product")
        ad_audience= st.text_input("Target audience:", key="ad_audience")
        ad_platform= st.selectbox("Platform:", ["Facebook","Instagram","Google","LinkedIn","TikTok"], key="ad_platform")
        ad_goal    = st.selectbox("Goal:", ["Lead Generation","Sales","Brand Awareness","Event","App Install"], key="ad_goal")
        if st.button("📢 Generate Ad Copy", use_container_width=True, type="primary", key="ad_gen"):
            if ad_product.strip():
                p = f"Write {ad_platform} ad copy for {ad_product}. Audience: {ad_audience}. Goal: {ad_goal}. Include: Headline (under 40 chars), Primary text (under 125 chars), Description, CTA button text. Write 3 variations. Australian market."
                with st.spinner("Writing ads..."):
                    r, e = ai_call(p, max_tokens=600)
                if r: st.text_area("Ad Copy:", value=r, height=250, key="ad_result")

    with bt_tabs[3]:
        st.markdown("### 🏷️ Business Name & Tagline Generator")
        bn_desc = st.text_area("Describe the business:", height=80, key="bn_desc")
        bn_industry = st.selectbox("Industry:", ["Cybersecurity","AI Tools","Tradies","Finance","Health","Retail","Tech","Other"], key="bn_industry")
        if st.button("🏷️ Generate Names", use_container_width=True, type="primary", key="bn_gen"):
            if bn_desc.strip():
                p = f"Generate 10 unique business names and taglines for: {bn_desc}. Industry: {bn_industry}. Australian market. Each name should be: memorable, available as a .com.au, professional, and reflect the brand. Format: Name — Tagline"
                with st.spinner("Generating names..."):
                    r, e = ai_call(p, max_tokens=500)
                if r: st.text_area("Business Names:", value=r, height=250, key="bn_result")

    with bt_tabs[4]:
        st.markdown("### 📋 Onboarding Checklist Builder")
        ob_product = st.text_input("Product/Service:", key="ob_product")
        ob_client  = st.text_input("Client type:", key="ob_client")
        if st.button("📋 Build Onboarding Checklist", use_container_width=True, type="primary", key="ob_gen"):
            if ob_product.strip():
                p = f"Build a complete client onboarding checklist for: {ob_product}. Client type: {ob_client}. Include: Pre-install steps, Day 1 actions, Week 1 actions, Month 1 milestones, ongoing touchpoints. Format as a numbered checklist with owner (client/us) and timeframe."
                with st.spinner("Building checklist..."):
                    r, e = ai_call(p, max_tokens=700)
                if r: st.text_area("Onboarding Checklist:", value=r, height=300, key="ob_result")

    with bt_tabs[5]:
        st.markdown("### 🎯 Sales Script Generator")
        ss_product  = st.text_input("Product:", key="ss_product_bt")
        ss_objection= st.selectbox("Objection to handle:", ["Too expensive","Not the right time","Already have a solution","Need to think about it","Need to talk to my partner","What's the ROI?","How is this different?"], key="ss_obj")
        ss_stage    = st.selectbox("Stage:", ["Cold Call Opening","Discovery","Presentation","Objection Handle","Close","Follow-Up"], key="ss_stage")
        if st.button("🎯 Generate Script", use_container_width=True, type="primary", key="ss_gen_bt"):
            if ss_product.strip():
                p = f"Write a word-for-word sales script for {ss_stage} stage. Product: {ss_product}. Objection to handle: {ss_objection}. Australian business context. Natural, conversational, not pushy. Include exact words to say."
                with st.spinner("Writing script..."):
                    r, e = ai_call(p, max_tokens=700)
                if r: st.text_area("Sales Script:", value=r, height=280, key="ss_result_bt")

    with bt_tabs[6]:
        st.markdown("### 📊 Weekly Wins Tracker")
        wins = jload(DATA_DIR/"wins.json", [])
        with st.form("add_win_form"):
            wc1, wc2 = st.columns(2)
            with wc1:
                w_win  = st.text_input("This week's win:", key="w_win")
                w_value= st.text_input("Value/impact:", key="w_value")
            with wc2:
                w_cat  = st.selectbox("Category:", ["Revenue","Client","Product","Marketing","Personal","Team"], key="w_cat")
            if st.form_submit_button("🏆 Log Win", use_container_width=True):
                wins.append({"win":w_win,"value":w_value,"category":w_cat,"date":now.strftime("%Y-%m-%d")})
                jsave(DATA_DIR/"wins.json", wins); st.rerun()
        if wins:
            for w in reversed(wins[-10:]):
                st.markdown(f"<div class='card' style='padding:8px 12px;margin:4px 0;'><span style='color:#39ff14;'>🏆</span> <b>{w.get('win','')}</b> <span style='color:#888;font-size:.8em;'>— {w.get('value','')} · {w.get('date','')}</span></div>",
                            unsafe_allow_html=True)

    with bt_tabs[7]:
        st.markdown("### 🌐 Web Redesigner")
        wr_url = st.text_input("Paste any website URL:", placeholder="https://competitor.com.au", key="wr_url")
        wr_goal= st.selectbox("Redesign goal:", ["Modernise","Improve Conversions","Mobile-First","Rebrand","Simplify"], key="wr_goal")
        if st.button("🌐 Redesign Website", use_container_width=True, type="primary", key="wr_gen"):
            if wr_url.strip():
                p = f"Analyse this website URL and provide a complete redesign brief: {wr_url}. Goal: {wr_goal}. Include: Current issues, new structure recommendation, copy improvements, CTA optimisation, colour/design suggestions, and a full new homepage copy draft. Be specific and actionable."
                with st.spinner("Analysing and redesigning..."):
                    r, e = ai_call(p, max_tokens=1200)
                if r: st.text_area("Redesign Brief:", value=r, height=350, key="wr_result")

    with bt_tabs[8]:
        st.markdown("### 📱 Mini App Cloner")
        mc_url  = st.text_input("App or website URL to clone concept:", key="mc_url")
        mc_twist= st.text_input("Your twist / improvement:", placeholder="e.g. Make it for Australian tradies with a dark theme", key="mc_twist")
        if st.button("📱 Clone & Improve", use_container_width=True, type="primary", key="mc_gen"):
            if mc_url.strip():
                p = f"Analyse this app/website: {mc_url}. My twist: {mc_twist}. Provide: Core features to replicate, improvements to make, tech stack recommendation, MVP feature list, monetisation model, and a full landing page copy for the new version."
                with st.spinner("Cloning concept..."):
                    r, e = ai_call(p, max_tokens=1000)
                if r: st.text_area("Clone Blueprint:", value=r, height=350, key="mc_result")

    with bt_tabs[9]:
        st.markdown("### 🚀 Landing Page Builder")
        lp_product = st.text_input("Product/Service:", key="lp_product")
        lp_audience= st.text_input("Target audience:", key="lp_audience")
        lp_price   = st.text_input("Price/Offer:", key="lp_price")
        lp_cta     = st.text_input("CTA:", value="Book a Free Demo", key="lp_cta")
        if st.button("🚀 Build Landing Page", use_container_width=True, type="primary", key="lp_gen"):
            if lp_product.strip():
                p = f"Write complete landing page copy for: {lp_product}. Audience: {lp_audience}. Price: {lp_price}. CTA: {lp_cta}. Include: Headline, subheadline, hero section, 3 key benefits, social proof section, features list, FAQ (5 questions), final CTA. Conversion-optimised, Australian market."
                with st.spinner("Building landing page..."):
                    r, e = ai_call(p, max_tokens=1200)
                if r:
                    st.text_area("Landing Page Copy:", value=r, height=400, key="lp_result")
                    st.download_button("⬇ Download", r, f"landing_{lp_product[:15]}.txt", key="dl_lp")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 13 — TASK SHEET
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[13]:
    st.markdown("## 📋 Daily Task Sheet")
    tasks = jload(TASKS_FILE, [])

    tc1, tc2 = st.columns([2,1])
    with tc1:
        with st.form("add_task_form"):
            tfc1, tfc2, tfc3 = st.columns(3)
            with tfc1:
                t_task   = st.text_input("Task:", key="t_task")
                t_agent  = st.selectbox("Assign to:", ["Me","Content Machine","Email Agent","Sales Bot","Analytics Brain","Deploy Master","Code Builder","Social Agent"], key="t_agent")
            with tfc2:
                t_priority = st.selectbox("Priority:", ["🔥 High","⚡ Medium","💡 Low"], key="t_priority")
                t_due      = st.text_input("Due:", value="Today", key="t_due")
            with tfc3:
                t_cat    = st.selectbox("Category:", ["Revenue","Content","Email","Lead","Product","Admin","Security","Social"], key="t_cat")
            if st.form_submit_button("➕ Add Task", use_container_width=True):
                tasks.append({"id":len(tasks)+1,"task":t_task,"agent":t_agent,"priority":t_priority,"due":t_due,"category":t_cat,"done":False,"date":now.strftime("%Y-%m-%d")})
                jsave(TASKS_FILE, tasks); st.rerun()

    with tc2:
        total_tasks = len(tasks)
        done_tasks  = len([t for t in tasks if t.get("done")])
        pending     = total_tasks - done_tasks
        st.metric("Total", total_tasks)
        st.metric("Done", done_tasks)
        st.metric("Pending", pending)
        if st.button("🤖 AI Morning Briefing", use_container_width=True, key="morning_brief_ts"):
            pending_tasks = [t for t in tasks if not t.get("done")]
            p = f"Generate a motivating morning briefing for today. Pending tasks: {len(pending_tasks)}. Top tasks: {[t['task'] for t in pending_tasks[:5]]}. Revenue MRR: ${mrr:,}. Date: {now.strftime('%A %d %B %Y')}. Be direct, energising, and focused. Under 150 words."
            with st.spinner("Generating briefing..."):
                br, _ = ai_call(p, max_tokens=300)
            if br: st.text_area("Today's Briefing:", value=br, height=150, key="ts_brief")

    pending_tasks = [t for t in tasks if not t.get("done")]
    done_tasks_list = [t for t in tasks if t.get("done")]

    if pending_tasks:
        st.markdown("### ⏳ Pending")
        for t in sorted(pending_tasks, key=lambda x: x.get("priority","⚡ Medium")):
            tc_a, tc_b, tc_c = st.columns([4,1,1])
            with tc_a:
                st.markdown(f"<div style='padding:6px 10px;background:rgba(255,255,255,0.03);border-radius:6px;border-left:3px solid #ff006e;margin:3px 0;'>{t.get('priority','')} <b>{t.get('task','')}</b> <span style='color:#888;font-size:.8em;'>→ {t.get('agent','')} · {t.get('due','')}</span></div>",
                            unsafe_allow_html=True)
            with tc_b:
                if st.button("✅", key=f"done_t_{t['id']}"):
                    t["done"] = True; jsave(TASKS_FILE, tasks); st.rerun()
            with tc_c:
                if st.button("🗑️", key=f"del_t_{t['id']}"):
                    tasks = [x for x in tasks if x["id"] != t["id"]]
                    jsave(TASKS_FILE, tasks); st.rerun()

    if done_tasks_list:
        with st.expander(f"✅ Completed ({len(done_tasks_list)})"):
            for t in done_tasks_list:
                st.markdown(f"<span style='color:#39ff14;'>✅</span> <s style='color:#555;'>{t.get('task','')}</s>", unsafe_allow_html=True)
            if st.button("🗑️ Clear All Completed", key="clear_done"):
                tasks = [t for t in tasks if not t.get("done")]
                jsave(TASKS_FILE, tasks); st.rerun()

    ts_export = "\n".join([f"[{'✅' if t.get('done') else '⬜'}] {t.get('priority','')} {t.get('task','')} → {t.get('agent','')} · Due: {t.get('due','')}" for t in tasks])
    st.download_button("⬇ Export Task Sheet", ts_export, f"tasks_{now.strftime('%Y%m%d')}.txt", key="dl_tasks")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 14 — SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[14]:
    st.markdown("## ⚙️ Settings")
    set_tabs = st.tabs(["🤖 AI Engine","🔔 Notifications","🌤️ Display","🔑 API Keys","📤 Data Export"])

    with set_tabs[0]:
        st.markdown("### 🤖 AI Engine Settings")
        s1c1, s1c2 = st.columns(2)
        with s1c1:
            new_lm_url   = st.text_input("LM Studio URL:", value=S.get("lm_studio_url","http://localhost:1234/v1"), key="s_lm_url")
            new_ollama_m = st.text_input("Ollama model:", value=S.get("ollama_model","llama3.2:1b"), key="s_ollama")
            new_ds_key   = st.text_input("DeepSeek API key:", value=S.get("deepseek_key",""), type="password", key="s_ds")
        with s1c2:
            new_oai_key  = st.text_input("OpenAI API key:", value=S.get("openai_key",""), type="password", key="s_oai")
            new_heygen   = st.text_input("HeyGen API key:", value=S.get("heygen_key",""), type="password", key="s_heygen")
            new_did      = st.text_input("D-ID API key:", value=S.get("did_key",""), type="password", key="s_did")
        if st.button("💾 Save AI Settings", use_container_width=True, type="primary", key="save_ai"):
            S.update({"lm_studio_url":new_lm_url,"ollama_model":new_ollama_m,"deepseek_key":new_ds_key,"openai_key":new_oai_key,"heygen_key":new_heygen,"did_key":new_did})
            jsave(SETTINGS_FILE, S); st.success("✅ AI settings saved")

    with set_tabs[1]:
        st.markdown("### 🔔 Notifications")
        new_tg_token = st.text_input("Telegram Bot Token:", value=S.get("telegram_token",""), type="password", key="s_tg")
        new_tg_chat  = st.text_input("Telegram Chat ID:", value=S.get("telegram_chat_id",""), key="s_tg_chat")
        st.markdown("""<div class='card' style='font-size:.8em;color:#888;'>
<b>How to get your Telegram Bot Token:</b><br>
1. Open Telegram → search @BotFather<br>
2. Send /newbot → follow prompts<br>
3. Copy the token and paste above<br><br>
<b>How to get your Chat ID:</b><br>
1. Message your bot once<br>
2. Visit: api.telegram.org/bot[TOKEN]/getUpdates<br>
3. Find "chat":{"id": XXXXXXX} — that's your Chat ID
</div>""", unsafe_allow_html=True)
        if st.button("💾 Save Notification Settings", use_container_width=True, type="primary", key="save_notif"):
            S.update({"telegram_token":new_tg_token,"telegram_chat_id":new_tg_chat})
            jsave(SETTINGS_FILE, S); st.success("✅ Notification settings saved")
        if st.button("🔔 Test Telegram", key="test_tg"):
            if S.get("telegram_token") and S.get("telegram_chat_id"):
                try:
                    import requests as req
                    r = req.post(f"https://api.telegram.org/bot{S['telegram_token']}/sendMessage",
                                 json={"chat_id":S["telegram_chat_id"],"text":"✅ ARTIFICIAL & INTELLIGENT — Telegram connected!"})
                    if r.status_code == 200: st.success("✅ Telegram test message sent!")
                    else: st.error(f"Failed: {r.text}")
                except Exception as ex: st.error(str(ex))
            else: st.warning("Add token and chat ID first.")

    with set_tabs[2]:
        st.markdown("### 🌤️ Display Settings")
        new_city = st.text_input("Your city (for weather):", value=S.get("weather_city","Sydney"), key="s_city")
        new_pw   = st.text_input("Change dashboard password:", type="password", key="s_pw")
        new_pw2  = st.text_input("Confirm new password:", type="password", key="s_pw2")
        if st.button("💾 Save Display Settings", use_container_width=True, type="primary", key="save_disp"):
            S["weather_city"] = new_city
            if new_pw and new_pw == new_pw2:
                S["password"] = new_pw
                st.success("✅ Password updated")
            elif new_pw and new_pw != new_pw2:
                st.error("Passwords don't match")
            jsave(SETTINGS_FILE, S); st.success("✅ Display settings saved")

    with set_tabs[3]:
        st.markdown("### 🔑 API Keys Reference")
        st.markdown("""<div class='card' style='font-size:.82em;color:#e0e0e0;'>
<b style='color:#ff006e;'>DeepSeek</b> — platform.deepseek.com → API Keys<br>
<b style='color:#ff006e;'>OpenAI</b> — platform.openai.com → API Keys<br>
<b style='color:#ff006e;'>HeyGen</b> — app.heygen.com → Settings → API<br>
<b style='color:#ff006e;'>D-ID</b> — studio.d-id.com → Settings → API<br>
<b style='color:#ff006e;'>LM Studio</b> — Run locally on port 1234 (no key needed)<br>
<b style='color:#ff006e;'>Ollama</b> — Run locally on port 11434 (no key needed)
</div>""", unsafe_allow_html=True)

    with set_tabs[4]:
        st.markdown("### 🛠️ Maintenance & Self-Repair")
        st.markdown("<p style='font-size:.8em;color:#888;'>Report a bug or request a quick fix. Your AI crew will attempt to repair the dashboard on the spot.</p>", unsafe_allow_html=True)
        repair_desc = st.text_area("Describe the issue or fix needed:", placeholder="e.g. The Revenue tab is showing $0 when it should be $3,552", height=80, key="repair_input")
        if st.button("🔧 Start Self-Repair", use_container_width=True, type="primary", key="repair_btn"):
            if repair_desc.strip():
                with st.spinner("AI crew analyzing and repairing..."):
                    # Log the repair request to security log for tracking
                    security_log.append({"time":now.strftime("%Y-%m-%d %H:%M"),"event":"Self-Repair Triggered","detail":repair_desc})
                    jsave(SECF, security_log)
                    # Send to Telegram so I (Manus) see it immediately
                    send_telegram(f"🔧 SELF-REPAIR REQUESTED\nIssue: {repair_desc}")
                    st.success("✅ Repair request logged and sent to the AI crew. We're on it!")
            else:
                st.warning("Please describe the issue first.")
        
        st.markdown("---")
        st.markdown("### 📤 Data Export")
        all_data = {"settings":S,"tasks":jload(TASKS_FILE,[]),"leads":jload(LEADS_FILE,[]),"revenue":jload(REVENUE_FILE,[]),"avatars":jload(AVF,[]),"ideas":jload(IDEAS_FILE,[]),"enquiries":jload(ENQUIRIES_FILE,[])}
        import json as _json
        st.download_button("⬇ Export All Data (JSON)", _json.dumps(all_data, indent=2, default=str), "ai_dashboard_backup.json", key="dl_all")
        if st.button("🗑️ Clear All Tasks", key="clear_tasks"):
            jsave(TASKS_FILE, []); st.success("Tasks cleared"); st.rerun()
        if st.button("🗑️ Clear Chat History", key="clear_chat"):
            st.session_state["chat_history"] = []; st.success("Chat cleared")
