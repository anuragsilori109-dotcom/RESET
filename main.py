import os
import time
import threading
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
OWNER_ID = os.getenv("OWNER_ID", "YOUR_TELEGRAM_ID")

# --- Reset Logic (fake endpoints for now) ---
def send_reset(email: str, method: str) -> str:
    try:
        # Example (replace with real logic)
        if method == "web":
            url = "https://example.com/reset_web"
        elif method == "api":
            url = "https://example.com/reset_api"
        else:
            url = "https://example.com/reset_mobile"

        # Fake request
        r = requests.post(url, data={"email": email}, timeout=5)
        if r.status_code == 200:
            return f"{method} ✅"
        else:
            return f"{method} ❌"
    except Exception as e:
        return f"{method} ❌ ({str(e)})"

def do_full_reset(email: str) -> str:
    methods = ["web", "api", "mobile"]
    results = [send_reset(email, m) for m in methods]
    return f"📧 {email}\n" + " | ".join(results)

# --- Commands ---
async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /reset email@example.com")
        return

    email = context.args[0]
    msg = do_full_reset(email)
    await update.message.reply_text(msg)

async def batch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /batch email1 email2 email3 ...")
        return

    emails = context.args
    await update.message.reply_text(f"🔁 Starting batch reset for {len(emails)} emails...")

    def worker(email):
        msg = do_full_reset(email)
        context.application.create_task(update.message.reply_text(msg))
        time.sleep(2)  # delay to avoid spam/flood

    threads = []
    for email in emails:
        t = threading.Thread(target=worker, args=(email,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

# --- Main ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("reset", reset_command))
    app.add_handler(CommandHandler("batch", batch_command))

    print("🤖 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
