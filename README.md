# Arbitrage Opportunities Telegram Bot

A Python Telegram bot that listens to Redis pub/sub for arbitrage opportunities and pushes notifications to subscribed users.

## Features

- 📡 Listens to Redis pub/sub channel for arbitrage opportunities
- 🤖 Telegram bot interface for user subscriptions
- 📢 Broadcasts opportunities to all subscribed users
- 🔄 Automatic reconnection on Redis connection loss
- ✅ User subscription management

## Prerequisites

- Python 3.7+
- Redis server running on localhost
- Telegram Bot Token (get from [@BotFather](https://t.me/botfather))

## Setup

1. **Clone/navigate to the project directory**

2. **Create a virtual environment** (optional but recommended):
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the bot**:
   - Copy `.env.example` to `.env`:
     ```bash
     copy .env.example .env
     ```
   - Edit `.env` and add your Telegram Bot Token:
     ```
     BOT_TOKEN=your_actual_bot_token_here
     ```

5. **Start Redis** (if not already running):
   ```bash
   redis-server
   ```

## Usage

### Start the Bot

```bash
python bot.py
```

### Telegram Bot Commands

- `/start` - Subscribe to arbitrage alerts
- `/stop` - Unsubscribe from alerts
- `/status` - Check subscription status

### Publishing Arbitrage Opportunities to Redis

To test or publish arbitrage opportunities, use Redis pub/sub:

**Using redis-cli:**
```bash
redis-cli PUBLISH arbitrage-opportunity '{"exchange_buy":"Binance","exchange_sell":"Coinbase","symbol":"BTC/USDT","buy_price":50000,"sell_price":50500,"profit_usd":500,"profit_percentage":1.0}'
```

**Using Python:**
```python
import redis
import json

r = redis.Redis(host='localhost', port=6379, db=0)
opportunity = {
    "exchange_buy": "Binance",
    "exchange_sell": "Coinbase",
    "symbol": "BTC/USDT",
    "buy_price": 50000,
    "sell_price": 50500,
    "profit_usd": 500,
    "profit_percentage": 1.0
}
r.publish('arbitrage-opportunity', json.dumps(opportunity))
```

## Configuration

Edit `.env` file to customize:

- `BOT_TOKEN` - Your Telegram Bot Token
- `REDIS_HOST` - Redis server host (default: localhost)
- `REDIS_PORT` - Redis server port (default: 6379)
- `REDIS_DB` - Redis database number (default: 0)
- `REDIS_CHANNEL` - Redis pub/sub channel name (default: arbitrage-opportunity)
- `LOG_LEVEL` - Logging level (default: INFO)

## Project Structure

```
arbitrage.report/
├── bot.py              # Main bot application
├── config.py           # Configuration management
├── requirements.txt    # Python dependencies
├── .env.example        # Example environment variables
├── .env                # Your actual configuration (create this)
└── README.md          # This file
```

## How It Works

1. The bot connects to your local Redis instance
2. It subscribes to the `arbitrage-opportunity` channel
3. Users can subscribe to the bot using `/start` command
4. When an arbitrage opportunity is published to Redis, the bot:
   - Receives the JSON data
   - Formats it into a readable message
   - Sends it to all subscribed users

## Error Handling

- Automatic reconnection to Redis on connection loss
- Removes blocked/deleted chats from subscriber list
- Logs all errors for debugging

## Example Message Format

When an arbitrage opportunity is detected, users receive:

```
🚨 Arbitrage Opportunity Detected!

Exchange Buy: Binance
Exchange Sell: Coinbase
Symbol: BTC/USDT
Buy Price: $50000.00
Sell Price: $50500.00
Profit Usd: $500.00
Profit Percentage: 1.00%
```

## Development

To modify the message format, edit the `format_arbitrage_message()` function in `bot.py`.

To add more commands, add new handler functions and register them in the `main()` function.

## Troubleshooting

- **Bot doesn't respond**: Check if your bot token is correct
- **No messages received**: Verify Redis is running and the channel name matches
- **Connection errors**: Ensure Redis is accessible on localhost:6379

## License

MIT License - feel free to use and modify as needed.
