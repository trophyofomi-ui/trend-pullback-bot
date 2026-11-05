def check_signal(df: pd.DataFrame, i: int, symbol: str) -> dict | None:
    if i < 250: return None
        
    t = df.iloc[i]
    prev = df.iloc[i-1]
    w = df.iloc[i-PULLBACK_WINDOW+1 : i+1]
    
    regime_long = bool(t.regime_long) and (t.ema50 > t.ema200)import pandas as pd

    regime_short = bool(t.regime_short)fromc
    
    # ETH requires a stronger trend (ADX > 28) because it chops more than BTC
    min_adx = 28.0 if "ETH" in symbol else ADX_MIN
    
    quality = (
        (t.adx14 > min_adx) and
        (t.atr_pct > ATR_PCT_FLOOR) and
        (t.atr_pct < ATR_PCT_CEIL_MULT * t.atr_pct_med)
    )
    
    # LONG SETUP
    if regime_long and quality:
        pullback = (w.low <= w.ema20).any()
        intact = t.close > t.ema20
        rsi_resume = (prev.rsi14 < RSI_LONG_DIP) and (t.rsi14 > RSI_LONG_DIP)
        trigger = t.close > prev.high
        
        if pullback and intact and rsi_resume and trigger:
            # Give ETH a wider stop-loss pad to avoid wick-hunting
            pad = 0.5 if "ETH" in symbol else STOP_ATR_PAD
            stop = df.low.iloc[i-STOP_LOOKBACK+1:i+1].min() - (pad * t.atr14)
            
            if (t.close - stop) <= (STOP_MAX_ATR * t.atr14):
                return {"side": "long", "bar": i, "entry": df.open.iloc[i+1], "stop": stop}
                
    # SHORT SETUP
    if regime_short and quality:
        pullback = (w.high >= w.ema20).any()
        intact = t.close < t.ema20
        rsi_resume = (prev.rsi14 > RSI_SHORT_DIP) and (t.rsi14 < RSI_SHORT_DIP)
        trigger = t.close < prev.low
        
        if pullback and intact and rsi_resume and trigger:
            # Give ETH a wider stop-loss pad
            pad = 0.5 if "ETH" in symbol else STOP_ATR_PAD
            stop = df.high.iloc[i-STOP_LOOKBACK+1:i+1].max() + (pad * t.atr14)
            
            if (stop - t.close) <= (STOP_MAX_ATR * t.atr14):
                return {"side": "short", "bar": i, "entry": df.open.iloc[i+1], "stop": stop}
                
    return None
