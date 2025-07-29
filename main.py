import os
import logging
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CallbackContext, CommandHandler
from telegram import Update

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_GROUP_ID = os.environ["ADMIN_GROUP_ID"]

application = ApplicationBuilder().token(BOT_TOKEN).build()


async def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        "Hi! Send me your suggestions and I'll forward them to the admins for review."
    )


async def handle_private_message(update: Update, context: CallbackContext) -> None:
    """Handle private messages (suggestions) from users."""
    if update.message.chat.type != "private":
        return

    await update.message.forward(ADMIN_GROUP_ID)    


if __name__ == "__main__":
    logger.info("Starting bot")
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, handle_private_message))
    application.run_polling()
