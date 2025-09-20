from typing import Final, Dict, Any, Optional
import setup_logging
import logging

import os
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from telegram.constants import ChatAction
from gemini import generate_marketing_captions, CaptionResponse

# States
ASK_IMAGE: Final[int] = 0
ASK_DESCRIPTION: Final[int] = 1
CHOOSE_CAPTION: Final[int] = 2

async def create_post_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[int]:
    """
    Entry point for the /createpost command.
    Asks user to upload an image.
    """
    if update.message is None:
        logging.warning("No message found in update; ignoring.")
        return ConversationHandler.END 

    await update.message.chat.send_action(action=ChatAction.TYPING)
    await update.message.reply_text("📸 Please upload the image of the product.")
    return ASK_IMAGE

async def ask_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the uploaded image and asks for a description.
    """
    if update.message is None:
        logging.warning("No message found in update; ignoring.")
        return ConversationHandler.END
    
    if context.user_data is None:
        logging.warning("No user_data found in context; initializing.")
        context.user_data = {}

    if update.message is None or not update.message.photo:
        await update.message.reply_text("❌ Please upload a valid image file.")
        return ASK_IMAGE
    
    # Get highest resolution photo
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)

    # Save locally
    image_path: str = os.path.join("downloads", f"{photo.file_unique_id}.jpg")
    os.makedirs("downloads", exist_ok=True)
    await file.download_to_drive(image_path)

    context.user_data["product_image"] = image_path

    await update.message.chat.send_action(action=ChatAction.TYPING)
    await update.message.reply_text(
        "📝 Now please provide a description of the product.\n\n"
        "Example:\n"
        "`Clay Vase - Target audience: Home decorators - Style: Elegant, warm tone - Purpose: Social media post`",
        parse_mode="Markdown"
    )
    return ASK_DESCRIPTION

async def generate_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the description and generates captions for user selection.
    """
    if update.message is None:
        logging.warning("No message found in update; ignoring.")
        return ConversationHandler.END

    if update.message is None or update.message.text is None:
        logging.warning("No description received.")
        await update.message.reply_text("❌ Please provide a valid description.")
        return ASK_DESCRIPTION

    description: str = update.message.text
    image_path: str = context.user_data.get("product_image", "") if context.user_data else ""

    if not image_path:
        await update.message.reply_text("❌ Missing product image, please restart with /createpost.")
        return ConversationHandler.END

    await update.message.chat.send_action(action=ChatAction.TYPING)
    await update.message.reply_text("🎨 Generating marketing captions...")

    # Generate captions using Gemini
    result: CaptionResponse = await generate_marketing_captions(image_path, description)

    if result["error"]:
        await update.message.reply_text(f"❌ Error: {result['error']}")
        return ConversationHandler.END

    if not result["captions"]:
        await update.message.reply_text("❌ No captions generated. Please try again.")
        return ConversationHandler.END

    # Store captions for later use
    if context.user_data is not None:
        context.user_data["captions"] = result["captions"]

    # Create inline keyboard for caption selection
    keyboard = [
        [InlineKeyboardButton(f"Caption {i+1}", callback_data=f"caption_{i}")]
        for i in range(len(result["captions"]))
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Format captions for display
    caption_text = "Please choose your preferred caption:\n\n"
    for i, caption in enumerate(result["captions"]):
        caption_text += f"*Caption {i+1}*:\n"
        caption_text += f"{caption['text']}\n"
        caption_text += f"{''.join(caption['emojis'])} "
        caption_text += f"{' '.join(caption['hashtags'])}\n\n"

    await update.message.reply_text(caption_text, reply_markup=reply_markup, parse_mode="Markdown")
    return CHOOSE_CAPTION

async def handle_caption_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the user's caption selection.
    """
    if update.callback_query is None:
        logging.warning("No callback_query found in update; ignoring.")
        return ConversationHandler.END

    query: CallbackQuery = update.callback_query
    if not query or query.data is None or query.message is None:
        return ConversationHandler.END

    await query.answer()

    choice = int(query.data.split("_")[1])
    if context.user_data and "captions" in context.user_data:
        selected_caption = context.user_data["captions"][choice]
        
        # Format the final post
        final_caption = (
            f"{selected_caption['text']}\n\n"
            f"{''.join(selected_caption['emojis'])}\n"
            f"{' '.join(selected_caption['hashtags'])}"
        )

        # Send the final post with image
        if "product_image" in context.user_data:
            with open(context.user_data["product_image"], "rb") as photo:
                await context.bot.send_photo(
                    chat_id=query.message.chat.id,
                    photo=photo,
                    caption=final_caption
                )

        await context.bot.send_message(chat_id=query.message.chat.id, text="✅ Post created successfully!")
    
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Cancels the createpost flow.
    """
    if update.message is None:
        logging.warning("No message found in update; ignoring.")
        return ConversationHandler.END
    
    await update.message.reply_text("❌ Post creation cancelled.")
    return ConversationHandler.END
