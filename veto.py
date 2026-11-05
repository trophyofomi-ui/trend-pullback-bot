import os
import json
from anthropic import Anthropic

SIMULATE = True
os.environ["ANTHROPIC_API_KEY"] = "YOUR_API_KEY_HERE"
client = Anthropic()

SYSTEM_PROMPT = "You are a risk manager. Veto bad trades."

def llm_veto(setup_data: dict) -> dict:
    if SIMULATE:
        side = setup_data.get("side")
        adx = setup_data.get("adx14", 0)
        rsi = setup_data.get("rsi14", 50)
        close = setup_data.get("close", 0)
        ema20 = setup_data.get("ema20", 1)
        
        dist_from_ema = abs(close - ema20) / ema20 * 100

        # 1. Weak Trend Veto (Keep this)
        if adx < 25:
            return {"veto": True, "reason": "Weak Trend"}
            
        # 2. Overextended Veto (Keep this)
        if dist_from_ema > 2.0:
            return {"veto": True, "reason": "Overextended"}

        # 3. Chasing the Top/Bottom Veto
        if side == "long" and rsi > 70:
            return {"veto": True, "reason": "RSI Overbought"}
        if side == "short" and rsi < 30:
            return {"veto": True, "reason": "RSI Oversold"}
            
        return {"veto": False, "reason": "Approved"}
    
    try:
        msg = client.messages.create(model="claude-3-5-sonnet-20241022", max_tokens=100, system=SYSTEM_PROMPT, messages=[{"role": "user", "content": json.dumps(setup_data)}])
        return json.loads(msg.content[0].text)
    except Exception as e:
        return {"veto": False, "reason": "Error"}
