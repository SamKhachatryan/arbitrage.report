"""
Telegram Bot for Arbitrage Trades
Listens to Redis pub/sub for arbitrage trade executions and summaries and sends them to subscribed users.
"""

import json
import logging
import asyncio
import os
from typing import Set, Dict
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

# Store the last messages to avoid duplicates (per channel)
last_messages: Dict[str, dict] = {
    'arbitrage-trade-execution': {},
    'arbitrage-trade-summary': {}
}

# Redis configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))

# Redis channels to subscribe to
REDIS_CHANNELS = ['arbitrage-trade-execution', 'arbitrage-trade-summary']

# Telegram Bot Token
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables. Please set it in .env file")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command"""
    chat_id = update.effective_chat.id
    subscribed_chats.add(chat_id)
    
    await update.message.reply_text(
        '🤖 Welcome to Arbitrage Trade Alerts Bot!\n\n'
        'You will now receive arbitrage trade executions and summaries in real-time.\n\n'
        'Commands:\n'
        '/start - Subscribe to trade alerts\n'
        '/stop - Unsubscribe from alerts\n'
        '/status - Check subscription status'
    )
    logger.info(f"Chat {chat_id} subscribed to trade alerts")


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


async def format_trade_message(data: dict, channel: str) -> str:
    """Format the trade data into a readable message"""
    try:
        # Determine message type
        if 'execution' in channel:
            icon = "⚡"
            title = "*Trade Execution*"
        else:
            icon = "📊"
            title = "*Trade Summary*"
        
        message = f"{icon} {title}\n\n"
        
        # Format specific fields
        exchange = data.get('exchange', 'N/A').upper()
        pair = data.get('pair', 'N/A').upper()
        side = data.get('side', 'N/A').replace('_', ' ').title()
        action = data.get('action', 'N/A').upper()
        amount = data.get('amount', 0)
        price = data.get('price', 0)
        spread = data.get('spread_pct', 0)
        timestamp = data.get('timestamp', 'N/A')
        
        message += f"*Exchange:* {exchange}\n"
        message += f"*Pair:* {pair}\n"
        message += f"*Side:* {side}\n"
        message += f"*Action:* {action}\n"
        message += f"*Amount:* {amount:.2f}\n"
        message += f"*Price:* ${price:.2f}\n"
        message += f"*Spread:* {spread:.2f}%\n"
        message += f"*Time:* {timestamp}\n"
        
        return message
    except Exception as e:
        logger.error(f"Error formatting message: {e}")
        return f"{icon} *New Trade*\n\n```json\n{json.dumps(data, indent=2)}\n```"


async def redis_listener(application: Application) -> None:
    """Listen to Redis pub/sub channels for arbitrage trades"""
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
            
            # Subscribe to both channels
            pubsub = r.pubsub()
            await pubsub.subscribe(*REDIS_CHANNELS)
            logger.info(f"Subscribed to Redis channels: {', '.join(REDIS_CHANNELS)}")
            
            # Listen for messages using get_message instead of async iteration
            while True:
                try:
                    message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                    
                    if message is not None and message['type'] == 'message':
                        try:
                            channel = message['channel']
                            
                            # Parse the JSON data
                            data = json.loads(message['data'])
                            logger.info(f"Received trade from {channel}: {data}")
                            
                            # Check if this message is the same as the last one for this channel
                            if data == last_messages.get(channel, {}):
                                logger.info(f"Duplicate message on {channel}, skipping...")
                                continue
                            
                            # Update the last message for this channel
                            last_messages[channel] = data.copy()
                            
                            # Format the message
                            formatted_message = await format_trade_message(data, channel)
                            
                            # Send to all subscribed chats
                            for chat_id in subscribed_chats.copy():
                                try:
                                    await application.bot.send_message(
                                        chat_id=chat_id,
                                        text=formatted_message,
                                        parse_mode='Markdown'
                                    )
                                    logger.info(f"Sent {channel} message to chat {chat_id}")
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
