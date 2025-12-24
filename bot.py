"""
Telegram Bot for Arbitrage Opportunities
Listens to Redis pub/sub for arbitrage opportunities and sends them to subscribed users.
"""

import json
import logging
import asyncio
import os
from typing import Set
from dotenv import load_dotenv
import redis.asyncio as redis
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Store subscribed chat IDs
subscribed_chats: Set[int] = set()

# Store the last opportunity to avoid duplicates
last_opportunity: dict = {}

# Redis configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_CHANNEL = os.getenv('REDIS_CHANNEL', 'arbitrage-opportunity')

# Telegram Bot Token
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables. Please set it in .env file")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command"""
    chat_id = update.effective_chat.id
    subscribed_chats.add(chat_id)
    
    await update.message.reply_text(
        '🤖 Welcome to Arbitrage Opportunities Bot!\n\n'
        'You will now receive arbitrage opportunities as they are detected.\n\n'
        'Commands:\n'
        '/start - Subscribe to arbitrage alerts\n'
        '/stop - Unsubscribe from alerts\n'
        '/status - Check subscription status'
    )
    logger.info(f"Chat {chat_id} subscribed to arbitrage alerts")


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /stop command"""
    chat_id = update.effective_chat.id
    
    if chat_id in subscribed_chats:
        subscribed_chats.remove(chat_id)
        await update.message.reply_text(
            '👋 You have been unsubscribed from arbitrage alerts.\n'
            'Use /start to subscribe again.'
        )
        logger.info(f"Chat {chat_id} unsubscribed from arbitrage alerts")
    else:
        await update.message.reply_text(
            'You are not currently subscribed.\n'
            'Use /start to subscribe to arbitrage alerts.'
        )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /status command"""
    chat_id = update.effective_chat.id
    
    if chat_id in subscribed_chats:
        await update.message.reply_text(
            '✅ You are subscribed to arbitrage alerts.\n'
            f'Total subscribers: {len(subscribed_chats)}'
        )
    else:
        await update.message.reply_text(
            '❌ You are not subscribed to arbitrage alerts.\n'
            'Use /start to subscribe.'
        )


async def format_arbitrage_message(data: dict) -> str:
    """Format the arbitrage opportunity data into a readable message"""
    try:
        message = "🚨 *Arbitrage Opportunity Detected!*\n\n"
        
        # Add all key-value pairs from the JSON
        for key, value in data.items():
            # Format the key to be more readable
            formatted_key = key.replace('_', ' ').title()
            
            # Handle different value types
            if isinstance(value, (int, float)):
                if 'price' in key.lower() or 'profit' in key.lower():
                    message += f"*{formatted_key}:* ${value:.2f}\n"
                elif 'percentage' in key.lower() or 'percent' in key.lower():
                    message += f"*{formatted_key}:* {value:.2f}%\n"
                else:
                    message += f"*{formatted_key}:* {value}\n"
            else:
                message += f"*{formatted_key}:* {value}\n"
        
        return message
    except Exception as e:
        logger.error(f"Error formatting message: {e}")
        return f"🚨 *Opportunity*\n\n```json\n{json.dumps(data, indent=2)}\n```"


async def redis_listener(application: Application) -> None:
    """Listen to Redis pub/sub channel for arbitrage opportunities"""
    logger.info("Starting Redis listener...")
    
    while True:
        try:
            # Connect to Redis
            r = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                decode_responses=True
            )
            
            # Subscribe to the channel
            pubsub = r.pubsub()
            await pubsub.subscribe(REDIS_CHANNEL)
            logger.info(f"Subscribed to Redis channel: {REDIS_CHANNEL}")
            
            # Listen for messages using get_message instead of async iteration
            while True:
                try:
                    message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                    
                    if message is not None and message['type'] == 'message':
                        try:
                            # Parse the JSON data
                            data = json.loads(message['data'])
                            logger.info(f"Received arbitrage opportunity: {data}")
                            
                            # Check if this opportunity is the same as the last one
                            if data == last_opportunity:
                                logger.info("Duplicate opportunity detected, skipping...")
                                continue
                            
                            # Update the last opportunity
                            last_opportunity.clear()
                            last_opportunity.update(data)
                            
                            # Format the message
                            formatted_message = await format_arbitrage_message(data)
                            
                            # Send to all subscribed chats
                            for chat_id in subscribed_chats.copy():
                                try:
                                    await application.bot.send_message(
                                        chat_id=chat_id,
                                        text=formatted_message,
                                        parse_mode='Markdown'
                                    )
                                    logger.info(f"Sent message to chat {chat_id}")
                                except Exception as e:
                                    logger.error(f"Error sending message to chat {chat_id}: {e}")
                                    # Remove chat if it's blocked or deleted
                                    if "bot was blocked" in str(e).lower() or "chat not found" in str(e).lower():
                                        subscribed_chats.discard(chat_id)
                                        logger.info(f"Removed chat {chat_id} from subscribers")
                        
                        except json.JSONDecodeError as e:
                            logger.error(f"Error decoding JSON: {e}")
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
                    
                    # Small delay to prevent CPU spinning
                    await asyncio.sleep(0.01)
                    
                except asyncio.TimeoutError:
                    # Timeout is normal, just continue listening
                    continue
            
        except redis.ConnectionError as e:
            logger.error(f"Redis connection error: {e}")
            logger.info("Retrying in 5 seconds...")
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Unexpected error in Redis listener: {e}")
            logger.info("Retrying in 5 seconds...")
            await asyncio.sleep(5)


async def post_init(application: Application) -> None:
    """Initialize the Redis listener after the bot starts"""
    # Start the Redis listener in the background
    asyncio.create_task(redis_listener(application))


def main() -> None:
    """Start the bot"""
    logger.info("Starting Arbitrage Bot...")
    
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("status", status))
    
    # Run the bot
    logger.info("Bot is running. Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    # Fix for Python 3.14+ event loop handling
    # In Python 3.14+, there's no event loop by default in the main thread
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        # No event loop exists, create one
        asyncio.set_event_loop(asyncio.new_event_loop())
    
    main()
