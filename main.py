from typing import Final

import setup_logging 
import logging

import os
from dotenv import load_dotenv

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

from gemini import get_gemini_response, SYSTEM_PROMPT
from utils import split_message

load_dotenv()

TOKEN: Final = os.getenv("TELEGRAM_BOT_TOKEN")
BOT_USERNAME: Final = os.getenv("BOT_USERNAME")



async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        logging.warning("No message found in update; ignoring.")
        return
    
    # First model introduction message
    initial_prompt = [
        {"role": "user", "parts": [{"text": SYSTEM_PROMPT}]}
    ]
    initial_message = await get_gemini_response(initial_prompt)

    logging.debug(f"context: {context.user_data}   ")

    if context.user_data is not None:   
        context.user_data["chat_history"] = [
            {"role": "user", "parts": [{"text": SYSTEM_PROMPT}]},
            {"role": "model", "parts": [{"text": initial_message}]}
        ]
        logging.info(f"Chat history initialized for user {update.message.from_user}")

    await update.message.reply_text(initial_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text("Available commands:\n/start - Start the bot\n/help - Show this help message")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    if update.message is None or update.message.text is None:
        logging.warning("No message or text found; ignoring.")
        return

    message_type: str = update.message.chat.type
    text: str = update.message.text

    await update.message.chat.send_action(action=ChatAction.TYPING)

    logging.info(f"Received message in {message_type}: {text}")

    if context.user_data is not None and "chat_history" not in context.user_data:
        context.user_data["chat_history"] = [
            {"role": "user", "parts": [{"text": SYSTEM_PROMPT}]}
        ]

    if context.user_data is not None:
        if message_type in ["group", "supergroup"]:
            if text and BOT_USERNAME  and BOT_USERNAME in text:
                user_message = text.replace(f"@{BOT_USERNAME}", "").strip()
                context.user_data["chat_history"].append(
                    {"role": "user", "parts": [{"text": user_message}]}
                )
                bot_response = await get_gemini_response(context.user_data["chat_history"])
                logging.info(f"Sending response: {bot_response}")
                for chunk in split_message(bot_response):
                    await update.message.reply_text(chunk)
            else:
                logging.info("Message does not mention the bot; ignoring.")
                return
        else:
            user_message = text.replace(f"@{BOT_USERNAME}", "").strip()
            context.user_data["chat_history"].append(
                    {"role": "user", "parts": [{"text": user_message}]}
                )
            bot_response = await get_gemini_response(context.user_data["chat_history"])
            logging.info(f"Sending response: {bot_response}")
            for chunk in split_message(bot_response):
                await update.message.reply_text(chunk)
    else:
        logging.error("No user_data found in context; cannot maintain chat history.")

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

    