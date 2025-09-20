from typing import Final, Dict, Any, Optional
import setup_logging
import logging

import os
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, InputMediaPhoto
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from telegram.constants import ChatAction
from gemini import generate_marketing_captions, CaptionResponse, generate_marketing_images, ImageResponse

# States
ASK_IMAGE: Final[int] = 0
ASK_DESCRIPTION: Final[int] = 1
CHOOSE_IMAGE: Final[int] = 2
CHOOSE_CAPTION: Final[int] = 3
SHOW_PREVIEW: Final[int] = 4

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
    image_path: str = os.path.join("tmp/received", f"{photo.file_unique_id}.jpg")
    os.makedirs("tmp/received", exist_ok=True)
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
    Handles the description, generates images and captions for user selection.
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

    await update.message.chat.send_action(action=ChatAction.UPLOAD_PHOTO)
    await update.message.reply_text("🎨 Generating product images...")

    # Generate images using Gemini
    result: ImageResponse = await generate_marketing_images(image_path, description)

    if result["error"]:
        await update.message.reply_text(f"❌ Error: {result['error']}")
        return ConversationHandler.END

    if not result["images"]:
        await update.message.reply_text("❌ No images generated. Please try again.")
        return ConversationHandler.END

    # Store images for later use
    if context.user_data is not None:
        context.user_data["generated_images"] = result["images"]
        context.user_data["current_image_index"] = 0

    # Create navigation keyboard
    keyboard = [
        [
            InlineKeyboardButton("⬅️", callback_data="prev_image"),
            InlineKeyboardButton("1/3", callback_data="image_info"),
            InlineKeyboardButton("➡️", callback_data="next_image")
        ],
        [
            InlineKeyboardButton("✅ SELECT", callback_data="select_image"),
            InlineKeyboardButton("🔄 RE-GENERATE", callback_data="regenerate_images"),
            InlineKeyboardButton("❌ CANCEL", callback_data="cancel_post")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send first image with navigation controls
    with open(result["images"][0]["filePath"], "rb") as photo:
        await update.message.reply_photo(
            photo=photo,
            caption="Please review the generated images and make your selection:\n\n"
                   "• Use ⬅️ ➡️ to navigate between images\n"
                   "• Click SELECT when you find the right image\n"
                   "• Click RE-GENERATE for new variations\n"
                   "• Click CANCEL to stop",
            reply_markup=reply_markup
        )

    return CHOOSE_IMAGE

async def handle_image_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle image navigation and selection callbacks.
    """
    if update.callback_query is None:
        logging.warning("No callback_query found in update; ignoring.")
        return ConversationHandler.END

    query: CallbackQuery = update.callback_query
    if not query or not query.message or context.user_data is None:
        return ConversationHandler.END

    await query.answer()
    
    if query.data == "cancel_post":
        await context.bot.send_message(chat_id=query.message.chat.id, text="❌ Post creation cancelled.")
        return ConversationHandler.END
    
    images = context.user_data.get("generated_images", [])
    current_idx = context.user_data.get("current_image_index", 0)
    
    if query.data == "next_image":
        current_idx = (current_idx + 1) % len(images)
    elif query.data == "prev_image":
        current_idx = (current_idx - 1) % len(images)
    elif query.data == "select_image":
        # Store selected image and proceed to caption generation
        context.user_data["selected_image"] = images[current_idx]
        return await generate_captions(update, context)
    elif query.data == "regenerate_images":
        # Regenerate images
        await context.bot.edit_message_caption(
            chat_id=query.message.chat.id,
            message_id=query.message.message_id,
            caption="🎨 Regenerating images..."
        )
        return await generate_post(update, context)

    context.user_data["current_image_index"] = current_idx
    
    # Update image and navigation buttons
    keyboard = [
        [
            InlineKeyboardButton("⬅️", callback_data="prev_image"),
            InlineKeyboardButton(f"{current_idx + 1}/3", callback_data="image_info"),
            InlineKeyboardButton("➡️", callback_data="next_image")
        ],
        [
            InlineKeyboardButton("✅ SELECT", callback_data="select_image"),
            InlineKeyboardButton("🔄 RE-GENERATE", callback_data="regenerate_images"),
            InlineKeyboardButton("❌ CANCEL", callback_data="cancel_post")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    with open(images[current_idx]["filePath"], "rb") as photo:
        await context.bot.edit_message_media(
            chat_id=query.message.chat.id,
            message_id=query.message.message_id,
            media=InputMediaPhoto(
                media=photo,
                caption="Please review the generated images and make your selection:\n\n"
                       "• Use ⬅️ ➡️ to navigate between images\n"
                       "• Click SELECT when you find the right image\n"
                       "• Click RE-GENERATE for new variations\n"
                       "• Click CANCEL to stop"
            ),
            reply_markup=reply_markup
        )

    return CHOOSE_IMAGE


async def generate_captions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Generate captions after image selection.
    """
    if update.callback_query is None:
        logging.warning("No callback_query found in update; ignoring.")
        return ConversationHandler.END

    if context.user_data is None:
        logging.warning("No user_data found in context; ignoring.")
        return ConversationHandler.END
    
    query: CallbackQuery = update.callback_query
    if not query or not query.message or context.user_data is None:
        return ConversationHandler.END

    await context.bot.send_message(chat_id=query.message.chat.id, text="✍️ Generating marketing captions...")

    selected_image_dict = context.user_data.get("selected_image")
    selected_image: str = selected_image_dict["filePath"] if selected_image_dict and "filePath" in selected_image_dict else ""
    description = context.user_data.get("description", "")

    # Generate captions using Gemini
    result: CaptionResponse = await generate_marketing_captions(
        selected_image, 
        description
    )

    if result["error"]:
        await context.bot.send_message(
            chat_id=query.message.chat.id,
            text=f"❌ Error: {result['error']}"
        )
        return ConversationHandler.END

    if not result["captions"]:
        await context.bot.send_message(chat_id=query.message.chat.id, text="❌ No captions generated. Please try again.")
        return ConversationHandler.END

    # Store captions for later use
    context.user_data["captions"] = result["captions"]

    # Create keyboard for caption selection
    keyboard = [
        [InlineKeyboardButton(f"Caption {i+1}", callback_data=f"caption_{i}")]
        for i in range(len(result["captions"]))
    ]
    keyboard.append([
        InlineKeyboardButton("🔄 RE-GENERATE", callback_data="regenerate_captions"),
        InlineKeyboardButton("❌ CANCEL", callback_data="cancel_post")
    ])
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Format captions for display
    caption_text = "Please choose your preferred caption:\n\n"
    for i, caption in enumerate(result["captions"]):
        caption_text += (
            f"*Caption {i+1}*:\n"
            f"{caption['text']}\n"
            f"{''.join(caption['emojis'])}\n"
            f"{' '.join(caption['hashtags'])}\n\n"
        )

    await context.bot.send_message(
        chat_id=query.message.chat.id,
        text=caption_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

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
