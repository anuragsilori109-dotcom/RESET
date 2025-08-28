import os, re, json, requests
from uuid import uuid4
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

# === KEEP_ALIVE ===
def keep_alive():
    app = Flask('')

    @app.route('/')
    def home():
        return "Bot is alive!"

    def run():
        app.run(host='0.0.0.0', port=8080)

    t = Thread(target=run)
    t.start()

# === RESET ALL APIs ===
def reset_all(user):
    results = []

    # === API 1: Web AJAX ===
    try:
        url = "https://www.instagram.com/accounts/account_recovery_send_ajax/"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.instagram.com/accounts/password/reset/",
            "X-CSRFToken": "csrftoken",
        }
        data = {"email_or_username": user, "recaptcha_challenge_field": ""}
        r = requests.post(url, headers=headers, data=data)

        if r.status_code == 200:
            match = re.search(r"<b>(.*?)</b>", r.text)
            if match:
                results.append(f"✅ Reset sent (Web1): {match.group(1)}")
            else:
                results.append("⚠️ Reset (Web1): No obfuscated email found")
        else:
            results.append(f"❌ Reset (Web1): HTTP {r.status_code}")
    except Exception as e:
        results.append(f"❌ Reset (Web1): {e}")

    # === API 2: Mobile API ===
    try:
        url_info = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={user}"
        headers_info = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
        resp = requests.get(url_info, headers=headers_info).json()
        user_id = resp["data"]["user"]["id"]

        url_reset = "https://i.instagram.com/api/v1/accounts/send_password_reset/"
        headers_reset = {"User-Agent": "Instagram 100.0.0.17.129 Android"}
        data = {"user_id": user_id, "device_id": str(uuid4())}
        r = requests.post(url_reset, headers=headers_reset, data=data).json()

        if "obfuscated_email" in r:
            results.append(f"✅ Reset sent (Mobile): {r['obfuscated_email']}")
        else:
            results.append(f"⚠️ Reset (Mobile): {r}")
    except Exception as e:
        results.append(f"❌ Reset (Mobile): {e}")

    # === API 3: Web v2 ===
    try:
        url = "https://www.instagram.com/api/v1/web/accounts/account_recovery_send_ajax/"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {"email_or_username": user, "flow": "fxcal"}
        r = requests.post(url, headers=headers, data=data).json()

        if r.get("status") == "ok":
            results.append(f"✅ Reset sent (Web2): {r.get('message','No message')}")
        elif r.get("status") == "fail":
            results.append(f"❌ Reset (Web2): {r.get('message','Failed')}")
        else:
            results.append(f"⚠️ Reset (Web2): {r}")
    except Exception as e:
        results.append(f"❌ Reset (Web2): {e}")

    return "\n".join(results)

# === COMMAND HANDLERS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Send /reset <username> to check reset email status via all APIs."
    )

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = " ".join(context.args)
    if not username:
        await update.message.reply_text("⚠️ Usage: /reset <username>")
        return

    await update.message.reply_text("🔄 Sending reset via all APIs...")
    result = reset_all(username)
    await update.message.reply_text(result)

# === MAIN ===
def main():
    keep_alive()
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset_command))

    app.run_polling()

if __name__ == "__main__":
    main()
