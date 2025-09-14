from typing import Final

import setup_logging 
import logging

import os
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

from gemini import get_gemini_response


load_dotenv()

TOKEN: Final = os.getenv("TELEGRAM_BOT_TOKEN")
BOT_USERNAME: Final = os.getenv("BOT_USERNAME")



async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is not None:
        await update.message.reply_text(f"Hello! I am {BOT_USERNAME}. How can I assist you today?")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is not None:
        await update.message.reply_text("Available commands:\n/start - Start the bot\n/help - Show this help message")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    if update.message is None or update.message.text is None:
        logging.warning("No message or text found; ignoring.")
        return

    message_type: str = update.message.chat.type
    text: str = update.message.text

    logging.info(f"Received message in {message_type}: {text}")

    if message_type in ["group", "supergroup"]:
        if text is not None and BOT_USERNAME is not None and BOT_USERNAME in text:
            user_message = text.replace(f"@{BOT_USERNAME}", "").strip()
            bot_response = await get_gemini_response(user_message)
            logging.info(f"Sending response: {bot_response}")
            await update.message.reply_text(bot_response)
        else:
            logging.info("Message does not mention the bot; ignoring.")
            return
    else:
        user_message = text.replace(f"@{BOT_USERNAME}", "").strip()
        bot_response = await get_gemini_response(user_message)
        logging.info(f"Sending response: {bot_response}")
        await update.message.reply_text(bot_response)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.error(f"An error occurred: {context.error} for Update: {update}")




if __name__ == "__main__":
    if TOKEN is None:
        raise ValueError("TELEGRAM_BOT_TOKEN is not set in environment variables.")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.add_error_handler(error_handler)

    logging.info("Bot is starting...")
    logging.info("Polling...")
    app.run_polling(poll_interval=3)

    