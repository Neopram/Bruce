
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Configuración de idioma
LANGUAGES = {
    "en": "English",
    "es": "Español",
    "zh": "中文",
    "hi": "हिन्दी",
    "fr": "Français",
    "ar": "العربية",
    "bn": "বাংলা",
    "ru": "Русский",
    "pt": "Português",
    "de": "Deutsch"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang_selection = "\n".join([f"/lang_{key} - {LANGUAGES[key]}" for key in LANGUAGES])
    await update.message.reply_text(f"Welcome {user.first_name}!\nSelect your language:\n{lang_selection}")

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_code = update.message.text.split("_")[1]
    if lang_code in LANGUAGES:
        await update.message.reply_text(f"Language set to {LANGUAGES[lang_code]}")
        os.environ["BOT_LANGUAGE"] = lang_code

app = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()

app.add_handler(CommandHandler("start", start))
for lang in LANGUAGES.keys():
    app.add_handler(CommandHandler(f"lang_{lang}", set_language))

app.run_polling()
