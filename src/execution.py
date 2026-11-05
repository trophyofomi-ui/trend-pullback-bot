import ccxt
import time

def get_execution_client(api_key="", api_secret=""):
    # We are creating a "Fake" exchange for testing purposes.
    # This allows you to test your bot logic without dealing with Bybit's buggy RSA keys.
    exchange = ccxt.bybit({
        'apiKey': 'fake_key',
        'secret': 'fake_secret',
        'enableRateLimit': True,
    })
    # We tell CCXT to simulate the orders locally
    exchange.set_sandbox_mode(True)
    return exchange

def place_order(symbol, side, size, stop_price, current_price):
    """Simulates placing a real order and taking profit."""
    
    print(f"\n🚀 [MOCK EXCHANGE] EXECUTING {side.upper()} ORDER FOR {symbol}")
    print(f"Position Size: {size:.4f}")
    print(f"Entry Price: ${current_price:.2f}")
    print(f"Stop Loss: ${stop_price:.2f}")
    
    # Simulate the time it takes to place an order
    time.sleep(1) 
    
    print(f"✅ Order Filled at ${current_price:.2f}!")
    print(f"🛡️ Stop Loss set at ${stop_price:.2f}!")
    
    return True
