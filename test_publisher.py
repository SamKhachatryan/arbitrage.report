"""
Test script to publish arbitrage trades to Redis
Run this to test the Telegram bot
"""

import redis
import json
import time

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0)

# Test trade execution data
test_executions = [
    {
        "exchange": "binance",
        "pair": "btc-usdt",
        "side": "spot_long",
        "action": "open",
        "amount": 100.5,
        "price": 43250.75,
        "spread_pct": 1.25,
        "timestamp": "2025-12-27T14:30:45Z"
    },
    {
        "exchange": "coinbase",
        "pair": "eth-usdt",
        "side": "spot_short",
        "action": "close",
        "amount": 50.25,
        "price": 2250.50,
        "spread_pct": 0.85,
        "timestamp": "2025-12-27T14:31:15Z"
    }
]

# Test trade summary data
test_summaries = [
    {
        "exchange": "binance",
        "pair": "btc-usdt",
        "side": "spot_long",
        "action": "open",
        "amount": 100.5,
        "price": 43250.75,
        "spread_pct": 1.25,
        "timestamp": "2025-12-27T14:30:45Z"
    },
    {
        "exchange": "kraken",
        "pair": "sol-usdt",
        "side": "futures_long",
        "action": "open",
        "amount": 200.0,
        "price": 95.30,
        "spread_pct": 2.15,
        "timestamp": "2025-12-27T14:32:00Z"
    }
]

def publish_trade(channel, trade_data):
    """Publish a trade to Redis"""
    try:
        # Publish to the specified channel
        r.publish(channel, json.dumps(trade_data))
        print(f"✅ Published to {channel}:")
        print(f"   {trade_data['exchange'].upper()} | {trade_data['pair'].upper()} | {trade_data['action'].upper()}")
        print(f"   Amount: {trade_data['amount']} @ ${trade_data['price']} | Spread: {trade_data['spread_pct']}%")
    except Exception as e:
        print(f"❌ Error publishing: {e}")

def main():
    print("🧪 Redis Arbitrage Trade Test Publisher")
    print("=" * 60)
    
    # Check Redis connection
    try:
        r.ping()
        print("✅ Connected to Redis")
    except redis.ConnectionError:
        print("❌ Cannot connect to Redis. Make sure Redis is running on localhost:6379")
        return
    
    print("\nPublishing test trades...")
    print("=" * 60)
    
    # Publish trade executions
    print("\n📤 TRADE EXECUTIONS:")
    print("-" * 60)
    for i, execution in enumerate(test_executions, 1):
        print(f"\n[Execution {i}/{len(test_executions)}]")
        publish_trade('arbitrage-trade-execution', execution)
        time.sleep(2)
    
    # Publish trade summaries
    print("\n\n📊 TRADE SUMMARIES:")
    print("-" * 60)
    for i, summary in enumerate(test_summaries, 1):
        print(f"\n[Summary {i}/{len(test_summaries)}]")
        publish_trade('arbitrage-trade-summary', summary)
        time.sleep(2)
    
    print("\n" + "=" * 60)
    print("✅ All test trades published!")
    print("\nCheck your Telegram bot for the messages.")

if __name__ == '__main__':
    main()
