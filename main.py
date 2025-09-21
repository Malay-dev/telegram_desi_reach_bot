from typing import Final

import setup_logging 
import logging

import os
from dotenv import load_dotenv

from fastapi import FastAPI, Request

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler, CallbackQueryHandler

from gemini import get_gemini_response, SYSTEM_PROMPT
from create_post import create_post_command, generate_post, ask_description, handle_image_navigation, handle_caption_choice, cancel, ASK_IMAGE, ASK_DESCRIPTION, CHOOSE_CAPTION, CHOOSE_IMAGE
from utils import split_message

load_dotenv()

TOKEN: Final = os.getenv("TELEGRAM_BOT_TOKEN")
BOT_USERNAME: Final = os.getenv("BOT_USERNAME")



async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        logging.warning("No message found in update; ignoring.")
        return
    
    await update.message.chat.send_action(action=ChatAction.TYPING)

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

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        logging.warning("No message found in update; ignoring.")
        return
    
    await update.message.chat.send_action(action=ChatAction.TYPING)

    if context.user_data is not None:
        context.user_data["chat_history"] = [
            {"role": "user", "parts": [{"text": SYSTEM_PROMPT}]}
        ]
        logging.info(f"Chat history cleared for user {update.message.from_user}")
    
    if update.message:
        await update.message.reply_text("Chat history cleared.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        logging.warning("No message found in update; ignoring.")
        return
    
    await update.message.chat.send_action(action=ChatAction.TYPING)

    await update.message.reply_text(
        """
        Available commands:\n
        /start - Begin interacting with the bot\n
        /clear - Reset the conversation context\n
        /create_post - Generate a social media post using your product image and description\n
        /help - Display all available commands\n
        """
    )



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





if TOKEN is None:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set in environment variables.")

app = ApplicationBuilder().token(TOKEN).build()

create_post_conv = ConversationHandler(
    entry_points=[CommandHandler("create_post", create_post_command)],
    states={
        ASK_IMAGE: [MessageHandler(filters.PHOTO, ask_description)],
        ASK_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, generate_post)],
        CHOOSE_IMAGE: [
            CallbackQueryHandler(handle_image_navigation, pattern='^(prev_image|next_image|select_image|regenerate_images|cancel_post)$')
        ],
        CHOOSE_CAPTION: [
            CallbackQueryHandler(handle_caption_choice, pattern='^caption_[0-2]$'),
            CallbackQueryHandler(generate_post, pattern='^regenerate_captions$'),
            CallbackQueryHandler(cancel, pattern='^cancel_post$')
        ]
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    allow_reentry=True
)

app.add_handler(CommandHandler("start", start_command))
app.add_handler(CommandHandler("clear", clear_command))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(create_post_conv)
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.add_error_handler(error_handler)

logging.info("Bot is starting...")
logging.info("Polling...")
# app.run_polling(poll_interval=3, allowed_updates=Update.ALL_TYPES)

server = FastAPI()

@server.get("/health")
async def health_check():
    return {"status": "ok"}

@server.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, app.bot)
    await app.process_update(update)
    return {"ok": True}