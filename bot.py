import logging
from telegram import Update, ForceReply
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
import os

# Enable logging

logging.basicConfig(
format=”%(asctime)s - %(name)s - %(levelname)s - %(message)s”,
level=logging.INFO
)
logger = logging.getLogger(**name**)

# Conversation states

API_ID, API_HASH, PHONE_NUMBER, CODE, PASSWORD = range(5)

# Store user data temporarily (in production, use a database)

user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
“”“Start the conversation and ask for API ID.”””
user_id = update.effective_user.id
user_data[user_id] = {}

```
await update.message.reply_text(
    "Welcome to the Telegram Session Connection Bot!\n\n"
    "I'll help you connect a session to your Telegram account.\n\n"
    "First, please provide your API ID.\n"
    "You can get it from https://my.telegram.org/apps\n\n"
    "Send /cancel to stop the process at any time."
)
return API_ID
```

async def api_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
“”“Store API ID and ask for API Hash.”””
user_id = update.effective_user.id
text = update.message.text.strip()

```
if not text.isdigit():
    await update.message.reply_text("API ID must be a number. Please try again:")
    return API_ID

user_data[user_id]["api_id"] = int(text)
await update.message.reply_text(
    "Great! Now please provide your API Hash.\n"
    "You can find it on the same page: https://my.telegram.org/apps"
)
return API_HASH
```

async def api_hash(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
“”“Store API Hash and ask for phone number.”””
user_id = update.effective_user.id
text = update.message.text.strip()

```
user_data[user_id]["api_hash"] = text
await update.message.reply_text(
    "Perfect! Now please provide your phone number.\n"
    "Format: +1234567890 (with country code)"
)
return PHONE_NUMBER
```

async def phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
“”“Store phone number and request verification code.”””
user_id = update.effective_user.id
phone = update.message.text.strip()

```
user_data[user_id]["phone"] = phone

# Create Telegram client
api_id = user_data[user_id]["api_id"]
api_hash = user_data[user_id]["api_hash"]

try:
    client = TelegramClient(f"session_{user_id}", api_id, api_hash)
    await client.connect()
    
    # Send code request
    await client.send_code_request(phone)
    user_data[user_id]["client"] = client
    
    await update.message.reply_text(
        "A verification code has been sent to your Telegram account.\n"
        "Please enter the code (example: 12345):"
    )
    return CODE
    
except Exception as e:
    logger.error(f"Error during code request: {e}")
    await update.message.reply_text(
        f"Error: {str(e)}\n\n"
        "Please check your API credentials and try again with /start"
    )
    if user_id in user_data:
        del user_data[user_id]
    return ConversationHandler.END
```

async def verification_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
“”“Process verification code and attempt to sign in.”””
user_id = update.effective_user.id
code = update.message.text.strip()

```
client = user_data[user_id]["client"]
phone = user_data[user_id]["phone"]

try:
    await client.sign_in(phone, code)
    
    # Get account info
    me = await client.get_me()
    
    await update.message.reply_text(
        f"✅ Successfully connected!\n\n"
        f"Account: {me.first_name} {me.last_name or ''}\n"
        f"Username: @{me.username or 'N/A'}\n"
        f"Phone: {me.phone}\n"
        f"Session file: session_{user_id}.session\n\n"
        "Your session has been saved!"
    )
    
    await client.disconnect()
    if user_id in user_data:
        del user_data[user_id]
    
    return ConversationHandler.END
    
except SessionPasswordNeededError:
    await update.message.reply_text(
        "Your account has 2FA enabled.\n"
        "Please enter your password:"
    )
    return PASSWORD
    
except Exception as e:
    logger.error(f"Error during sign in: {e}")
    await update.message.reply_text(
        f"Error: {str(e)}\n\n"
        "Please try again with /start"
    )
    await client.disconnect()
    if user_id in user_data:
        del user_data[user_id]
    return ConversationHandler.END
```

async def password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
“”“Process 2FA password.”””
user_id = update.effective_user.id
pwd = update.message.text

```
# Delete the password message for security
await update.message.delete()

client = user_data[user_id]["client"]

try:
    await client.sign_in(password=pwd)
    
    # Get account info
    me = await client.get_me()
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"✅ Successfully connected!\n\n"
             f"Account: {me.first_name} {me.last_name or ''}\n"
             f"Username: @{me.username or 'N/A'}\n"
             f"Phone: {me.phone}\n"
             f"Session file: session_{user_id}.session\n\n"
             "Your session has been saved!"
    )
    
    await client.disconnect()
    if user_id in user_data:
        del user_data[user_id]
    
    return ConversationHandler.END
    
except Exception as e:
    logger.error(f"Error with password: {e}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Error: {str(e)}\n\nPlease try again with /start"
    )
    await client.disconnect()
    if user_id in user_data:
        del user_data[user_id]
    return ConversationHandler.END
```

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
“”“Cancel the conversation.”””
user_id = update.effective_user.id

```
if user_id in user_data and "client" in user_data[user_id]:
    await user_data[user_id]["client"].disconnect()

if user_id in user_data:
    del user_data[user_id]

await update.message.reply_text(
    "Operation cancelled. Use /start to begin again."
)
return ConversationHandler.END
```

def main():
“”“Start the bot.”””
# Replace with your bot token
BOT_TOKEN = “YOUR_BOT_TOKEN_HERE”

```
application = Application.builder().token(BOT_TOKEN).build()

# Conversation handler
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        API_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, api_id)],
        API_HASH: [MessageHandler(filters.TEXT & ~filters.COMMAND, api_hash)],
        PHONE_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone_number)],
        CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, verification_code)],
        PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, password)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

application.add_handler(conv_handler)

# Start the bot
logger.info("Bot started!")
application.run_polling(allowed_updates=Update.ALL_TYPES)
```

if **name** == “**main**”:
main()
