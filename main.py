import os
import logging
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CallbackContext, CommandHandler, CallbackQueryHandler
from telegram import Update, InlineKeyboardButton, Message, InlineKeyboardMarkup, Bot

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_GROUP_ID = os.environ["ADMIN_GROUP_ID"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

application = ApplicationBuilder().token(BOT_TOKEN).build()
forwarded_messages = {}


async def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        "Hi! Send me your suggestions and I'll forward them to the admins for review."
    )


async def handle_private_message(update: Update, context: CallbackContext) -> None:
    """Handle private messages (suggestions) from users."""
    if update.message.chat.type != "private":
        return
    
    user = update.message.from_user
    user_info = f"{user.full_name} (@{user.username})" if user.username else user.full_name
    
    # Forward the message to admin group with approve/reject buttons
    forwarded_msg = await forward_to_admin_group(update.message, user_info, context.bot)
    
    # Store the relationship between forwarded message and original
    if forwarded_msg:
        forwarded_messages[forwarded_msg.message_id] = {
            "original_message": update.message,
            "user_info": user_info,
        }
        await update.message.reply_text("Thanks for your suggestion! Admins will review it soon.")


def forward_to_admin_group(message: Message, user_info: str, bot: Bot) -> Message:
    """Forward message to admin group with action buttons."""
    # Create keyboard with approve/reject buttons
    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{message.message_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{message.message_id}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    caption = f"Suggestion from {user_info}:\n\n{message.caption or 'Без подписи'}"

    # Handle different message types
    if message.photo:
        # For photos, send the photo with caption
        photo = message.photo[-1]  # Get highest resolution photo
        caption = caption
        return bot.send_photo(
            chat_id=ADMIN_GROUP_ID,
            photo=photo.file_id,
            caption=caption,
            reply_markup=reply_markup,
        )
    elif message.video:
        # For videos
        caption = caption
        return bot.send_video(
            chat_id=ADMIN_GROUP_ID,
            video=message.video.file_id,
            caption=caption,
            reply_markup=reply_markup,
        )
    elif message.document:
        # For documents
        caption = caption
        return bot.send_document(
            chat_id=ADMIN_GROUP_ID,
            document=message.document.file_id,
            caption=caption,
            reply_markup=reply_markup,
        )
    else:
        # For text messages
        text = f"Suggestion from {user_info}:\n\n{message.text}"
        return bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            text=text,
            reply_markup=reply_markup,
        )


async def handle_callback(update: Update, context: CallbackContext) -> None:
    """Handle the callback from Approve/Reject buttons."""
    query = update.callback_query
    data = query.data
    original_message_id = int(data.split('_')[1])
    
    # Get the stored message data
    message_data = forwarded_messages.get(query.message.message_id)
    if not message_data:
        await query.answer("This suggestion has already been processed or is invalid.")
        return
    
    original_message = message_data["original_message"]
    user_info = message_data["user_info"]
    
    if data.startswith("approve_"):
        # Approve action - post to channel
        await post_to_channel(original_message, user_info, context.bot)
        await query.answer("Suggestion approved and posted to channel!")
    elif data.startswith("reject_"):
        # Reject action - delete from admin group
        await query.answer("Suggestion rejected.")

    # Remove from storage
    await context.bot.delete_message(
        chat_id=ADMIN_GROUP_ID,
        message_id=query.message.message_id,
    )
    del forwarded_messages[query.message.message_id]

async def post_to_channel(message: Message, user_info: str, bot: Bot) -> None:
    """Post the approved message to the channel."""
    caption = f"Suggested by {user_info}{'\n\n' + message.caption if message.caption else ''}"
    if message.photo:
        photo = message.photo[-1]
        await bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=photo.file_id,
            caption=caption,
        )
    elif message.video:
        await bot.send_video(
            chat_id=CHANNEL_ID,
            video=message.video.file_id,
            caption=caption,
        )
    elif message.document:
        await bot.send_document(
            chat_id=CHANNEL_ID,
            document=message.document.file_id,
            caption=caption,
        )
    else:
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=f"{user_info}:\n\n{message.text}",
        )

if __name__ == "__main__":
    logger.info("Starting bot")
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, handle_private_message))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.run_polling()
