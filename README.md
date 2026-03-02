# ⚡ ARTIFICIAL & INTELLIGENT — AI Business Command Dashboard

**Your complete, all-in-one AI business dashboard. Built to run your entire operation from a single screen.**

This dashboard is a production-ready Streamlit application that combines a powerful AI chat interface, autonomous agent workflows, a full suite of business tools, and deep data tracking. It's designed to work both online (with OpenAI) and completely offline (with a local Llama model via LM Studio or Ollama).

## ✨ Features

| Feature | Description |
|---|---|
| **Triple-Engine AI** | Automatically uses **LM Studio** (for your local Hugging Face models), falls back to **Ollama**, then to **OpenAI GPT-4o-mini**. Always on, always smart. |
| **Command Chat** | A central chat interface that understands your business context. Assign tasks, get reports, write content, and strategize in a single thread. |
| **Autonomous Avatar Builder** | Go from a simple idea to a complete, monetizable online persona in one click. The AI builds the bio, scripts, content strategy, and action plan. |
| **AI Agent Crew** | A squad of specialized AI agents (Content, Email, Sales, etc.) that execute real tasks, from writing code to closing leads. |
| **Full Email Suite** | Comes pre-loaded with 20+ battle-tested email templates. Includes an AI auto-reply generator and a powerful AI email writer. |
| **Business & Web Tools** | A massive suite of tools including a **Podcast Studio**, **Web Redesigner**, **Mini App Cloner**, **Landing Page Builder**, **Invoice Generator**, **Proposal Machine**, and more. |
| **Data Persistence** | Everything is saved locally to JSON files in the `data/` directory. Your products, revenue, leads, and settings are never lost. |
| **Live Dashboard** | Real-time tracking of MRR, ARR, customers, leads, and product status. Includes revenue projections and milestone tracking. |
| **Notifications** | Get critical business alerts (revenue logged, tasks completed) sent directly to your phone via **Telegram**. |
| **100% Offline Capable** | If you have LM Studio or Ollama running, this entire dashboard works without an internet connection. |

---

## 🚀 Quickstart (Local Machine)

**Prerequisites:**
*   Python 3.9+ installed.
*   (Optional but Recommended) **LM Studio** installed and running for local AI.

### 1. Unzip the Files

Unzip the `ai_dashboard.zip` file into a folder.

### 2. Install Dependencies

Open your terminal in the `ai_dashboard` folder and run:

```bash
sudo pip3 install -r requirements.txt
```

This will install Streamlit, OpenAI, and all other necessary libraries.

### 3. (Optional) Setup Local AI with LM Studio

For 100% free, offline, private AI, you need to serve a model locally.

1.  **Download & Install LM Studio**: Get it from [lmstudio.ai](https://lmstudio.ai/).
2.  **Download a Model**: Inside LM Studio, search for a GGUF model. The one you provided was **`Llama-3.2-1B-Instruct-Q5_K_M.gguf`**. Any `Llama-3.2` or `Mistral` model is a great choice.
3.  **Start the Local Server**:
    *   Go to the "Local Server" tab (looks like `<->`).
    *   Select your downloaded model at the top.
    *   Click **Start Server**.

That's it. The dashboard will automatically connect to it on `http://localhost:1234`.

### 4. Run the Dashboard

In your terminal, from the `ai_dashboard` directory, run:

```bash
streamlit run app.py
```

Your browser will open with the dashboard running at `http://localhost:8501`.

---

## ⚙️ Configuration

All settings are managed in the **⚙️ Settings** tab of the dashboard.

*   **AI Engine**: Point the dashboard to your LM Studio or Ollama URLs. You can also add your OpenAI API key here to enable it as a fallback.
*   **Weather**: Get a free API key from [OpenWeatherMap](https://openweathermap.org/api) to enable the live weather widget.
*   **Telegram Notifications**: To get alerts on your phone:
    1.  Open Telegram and search for the `@BotFather`.
    2.  Send `/newbot` and follow the steps to create a bot. Copy the **token** it gives you.
    3.  Search for `@userinfobot` and send `/start`. Copy your **Chat ID**.
    4.  Paste the token and Chat ID into the Settings tab and save.

---

## 🌐 Deploy Online (Free)

1.  Push the `ai_dashboard` folder to a new GitHub repository.
2.  Go to [share.streamlit.io](https://share.streamlit.io).
3.  Connect your GitHub account, select the repository, and click **Deploy**.
4.  Your dashboard will be live on a public URL in minutes.

---

## 📁 File Structure

```
ai_dashboard/
├── app.py              # The main Streamlit application
├── requirements.txt    # Python dependencies
├── README.md           # This file
└── data/               # Auto-created on first run to store all your data
    ├── settings.json
    ├── products.json
    ├── revenue.json
    ├── tasks.json
    ├── avatars.json
    ├── leads.json
    ├── chat.json
    ├── tasksheet.json
    ├── wins.json
    └── clients.json
```
