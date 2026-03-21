from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola! Estoy funcionando correctamente.")

if __name__ == "__main__":
    app = Application.builder().token("7440694735:AAFouZltnblyopkAWr2Q1g4yOVupQOBg7wk").build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()
