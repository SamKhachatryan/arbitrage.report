"""
Test script to publish arbitrage opportunities to Redis
Run this to test the Telegram bot
"""

import redis
import json
import time

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0)

# Test arbitrage opportunity data
test_opportunities = [
    {
        "exchange_buy": "Binance",
        "exchange_sell": "Coinbase",
        "symbol": "BTC/USDT",
        "buy_price": 50000.00,
        "sell_price": 50500.00,
        "profit_usd": 500.00,
        "profit_percentage": 1.0,
        "timestamp": "2025-12-25 10:30:00"
    },
    {
        "exchange_buy": "Kraken",
        "exchange_sell": "Bitfinex",
        "symbol": "ETH/USDT",
        "buy_price": 3000.00,
        "sell_price": 3045.00,
        "profit_usd": 45.00,
        "profit_percentage": 1.5,
        "timestamp": "2025-12-25 10:31:00"
    },
    {
        "exchange_buy": "Bybit",
        "exchange_sell": "OKX",
        "symbol": "SOL/USDT",
        "buy_price": 100.00,
        "sell_price": 102.50,
        "profit_usd": 2.50,
        "profit_percentage": 2.5,
        "timestamp": "2025-12-25 10:32:00"
    }
]

def publish_opportunity(opportunity):
    """Publish an arbitrage opportunity to Redis"""
    try:
        # Publish to the arbitrage-opportunity channel
        r.publish('arbitrage-opportunity', json.dumps(opportunity))
        print(f"✅ Published: {opportunity['symbol']} - {opportunity['exchange_buy']} → {opportunity['exchange_sell']}")
        print(f"   Profit: ${opportunity['profit_usd']} ({opportunity['profit_percentage']}%)")
    except Exception as e:
        print(f"❌ Error publishing: {e}")

def main():
    print("🧪 Redis Arbitrage Opportunity Test Publisher")
    print("=" * 50)
    
    # Check Redis connection
    try:
        r.ping()
        print("✅ Connected to Redis")
    except redis.ConnectionError:
        print("❌ Cannot connect to Redis. Make sure Redis is running on localhost:6379")
        return
    
    print("\nPublishing test arbitrage opportunities...")
    print("=" * 50)
    
    # Publish each test opportunity with a delay
    for i, opportunity in enumerate(test_opportunities, 1):
        print(f"\n[{i}/{len(test_opportunities)}]")
        publish_opportunity(opportunity)
        
        if i < len(test_opportunities):
            print("\nWaiting 3 seconds before next opportunity...")
            time.sleep(3)
    
    print("\n" + "=" * 50)
    print("✅ All test opportunities published!")
    print("\nCheck your Telegram bot for the messages.")

if __name__ == '__main__':
    main()
