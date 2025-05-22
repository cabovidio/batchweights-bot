import logging
import datetime
import os
import json
import httpx
import asyncio
import subprocess

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)

# === Google Sheets Setup ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("Batches").worksheet("SoapWeights")

batch_data = {}

def parse_batch_number(batch_num):
    year = int(batch_num[0]) + 2020
    month = int(batch_num[1:3])
    day = int(batch_num[3:5])
    soap_code = batch_num[5:]
    date_str = datetime.date(year, month, day).isoformat()
    soap_type_map = {
        "ANA": "Annatto",
        "CHA": "Charcoal",
        "LAV": "Lavender",
        "EUC": "Eucalyptus",
    }
    soap_type = soap_type_map.get(soap_code, soap_code)
    return date_str, soap_type

def ai_interpret(text, chat_state):
    prompt = f"""
You are a helpful assistant for a soap maker. Interpret their message and return structured JSON only.

Sometimes the user will send:
- A batch number
- One or more weights (in grams)
- "End of batch"
Possibly all in the same message.

Return ONLY in JSON like this:

{{
  "actions": [
    {{"intent": "start_batch", "batch_number": "50630ANA", "reply": "..."}},
    {{"intent": "add_weight", "weight": 201, "reply": "..."}},
    {{"intent": "end_batch", "reply": "..."}}
  ]
}}

Message: "{text}"
Current batch: {chat_state.get("batch")}
Current weights: {chat_state.get("weights", [])}
"""

    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json",
        "Referer": "https://github.com/cabovidio",
        "X-Title": "SoapBatchBot",
        "User-Agent": "Mozilla/5.0"
    }

    payload = {
        "model": "mistralai/mixtral-8x7b-instruct",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2
    }

    try:
        r = httpx.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
        print("GPT RAW RESPONSE:", content)
        return json.loads(content)
    except Exception as e:
        print("OpenRouter ERROR:", e)
        return {"actions": [{"intent": "unknown", "reply": "Sorry, I didn’t understand that."}]}

async def transcribe_audio(filename):
    wav_file = filename.replace(".ogg", ".wav")
    try:
        subprocess.run(["ffmpeg", "-y", "-i", filename, wav_file], check=True)
        with open(wav_file, "rb") as f:
            files = {"file": ("audio.wav", f, "audio/wav")}
            r = httpx.post("https://openwhisper.freddy.dev/transcribe", files=files)
            if r.status_code == 200:
                result = r.json()
                return result.get("text", "")
            else:
                print("Transcription failed:", r.text)
    except Exception as e:
        print("Transcription error:", e)
    return ""

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    chat_id = update.effective_chat.id
    state = batch_data.get(chat_id, {})

    if update.message.voice:
        file = await context.bot.get_file(update.message.voice.file_id)
        await file.download_to_drive("voice.ogg")
        text = await transcribe_audio("voice.ogg")
        if not text:
            await update.message.reply_text("Sorry, I couldn't understand your voice message.")
            return
    elif update.message.text:
        text = update.message.text.strip()
    else:
        await update.message.reply_text("Please send a text or voice message.")
        return

    print("USER:", text)
    print("STATE:", state)

    result = ai_interpret(text, state)
    actions = result.get("actions", [])
    if not actions:
        await update.message.reply_text(result.get("reply", "Sorry, I didn’t understand that."))
        return

    for action in actions:
        intent = action.get("intent")
        reply = action.get("reply", "OK")

        if intent == "start_batch":
            batch_data[chat_id] = {"batch": action.get("batch_number"), "weights": []}
        elif intent == "add_weight":
            if chat_id not in batch_data or not batch_data[chat_id].get("batch"):
                await update.message.reply_text("Please tell me the batch number first.")
                continue
            batch_data[chat_id]["weights"].append(action["weight"])
        elif intent == "end_batch":
            if chat_id not in batch_data:
                await update.message.reply_text("No batch in progress.")
                continue
            batch_info = batch_data.pop(chat_id)
            batch_number = batch_info["batch"]
            weights = batch_info["weights"]
            if not weights:
                await update.message.reply_text("No weights recorded.")
                continue
            date_str, soap_type = parse_batch_number(batch_number)
            num = len(weights)
            avg = round(sum(weights) / num, 2)
            min_w = min(weights)
            max_w = max(weights)
            weights_str = ", ".join([str(w) for w in weights])
            row = [batch_number, date_str, soap_type, num, weights_str, avg, min_w, max_w]
            sheet.append_row(row)
            await update.message.reply_text(
                f"✅ Batch saved: {batch_number}\\n"
                f"{num} soaps — Avg: {avg}g | Min: {min_w}g | Max: {max_w}g"
            )
            continue
        await update.message.reply_text(reply)

async def main():
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
    app.add_handler(MessageHandler(filters.TEXT | filters.VOICE, handle_message))
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    import nest_asyncio

    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())

