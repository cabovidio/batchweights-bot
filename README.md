# 🧼 Karite Soap Batches Bot

This is a Telegram bot that lets you log handmade soap production batches using either text or **voice messages**. It records:

- Batch number (e.g., `50630ANA`)
- Individual soap weights
- Automatically calculates avg, min, max
- Saves to a **Google Sheet** called `Batches`, tab `SoapWeights`

---

## ✅ Features

- 🗣️ **Voice support** using free OpenWhisper transcription
- 💬 Natural language input (e.g. “weights are 104, 108, and 110g, end of batch”)
- 📄 Stores batches with one row per batch
- 📊 Google Sheets used as backend (via `gspread`)
- 🔌 OpenRouter AI model: `mistralai/mixtral-8x7b-instruct`
- 🧠 AI parses your message and replies contextually

---

## 🚀 Quick Start (Codespaces)

### 1. Clone the repo and enter your workspace

### 2. Create your `.env` file

```env
BOT_TOKEN=your_telegram_bot_token
OPENROUTER_API_KEY=your_openrouter_api_key
```

Then make sure `.env` is **excluded**:

```bash
echo ".env" >> .gitignore
```

### 3. Install requirements and tools

```bash
make setup
```

This will:
- Install `ffmpeg` (for converting Telegram voice messages)
- Install all Python dependencies from `requirements.txt`

---

## ▶️ Running the Bot

```bash
python bot.py
```

This runs the voice + text-enabled Telegram bot. It will reply in chat and store batches in Google Sheets.

---

## 📦 Files Overview

| File | Purpose |
|------|---------|
| `bot.py` | Main bot logic with text + voice support |
| `requirements.txt` | Python dependencies |
| `setup_voice.sh` | FFmpeg install script |
| `Makefile` | Combines `ffmpeg` and `pip install` setup |
| `.env.example` | Template for environment variables |

---

## 🧪 Try it on Telegram

Say or send a voice message:

> I made a batch of annatto today. The batch number is 50630ANA. Weights are 101, 102, 99. End of batch.

---

## 💸 Free Setup

- 🆓 Uses **OpenWhisper** (no account, free speech-to-text)
- 🆓 Uses **OpenRouter** (with free models like `mistralai/mixtral-8x7b-instruct`)
- 🆓 Works in **Codespaces** and on **Render free tier**

---

## 📋 Coming Soon

- Batch summaries
- Command-based UI
- Sheets/JSON export tools

---
