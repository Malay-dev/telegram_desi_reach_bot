from typing import Final


TELEGRAM_MAX_MESSAGE_LENGTH: Final = 4000

def split_message(text: str, chunk_size: int = TELEGRAM_MAX_MESSAGE_LENGTH):
    """Split text into chunks small enough for Telegram."""
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]