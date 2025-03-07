import json
from typing import Dict, Optional, Tuple
import pandas as pd
import streamlit as st
from apis import initialize_dhan_and_krutrim
from config import SEC_DICT
from services.data_service import get_data_from_db

def generate_trading_prompt(symbol: str) -> str:
    df = get_data_from_db(symbol, days=30)
    if df is None or df.empty:
        return f"Insufficient data for {symbol}"
    
    df['sma_20'] = df['close'].rolling(window=20).mean()
    df['sma_50'] = df['close'].rolling(window=50).mean()
    
    last_price = df['close'].iloc[-1]
    prev_price = df['close'].iloc[-2]
    price_change = (last_price - prev_price) / prev_price * 100
    
    recent_data = df.tail(5).reset_index().to_dict('records')
    
    for record in recent_data:
        for key, value in record.items():
            if isinstance(value, pd.Timestamp):
                record[key] = value.strftime('%Y-%m-%d %H:%M:%S')
    
    data_str = json.dumps(recent_data)
    
    prompt = f"""Analyze the following stock: {symbol}
    Current price: {last_price}
    Daily change: {price_change:.2f}%
    20-day SMA: {df['sma_20'].iloc[-1]:.2f}
    50-day SMA: {df['sma_50'].iloc[-1]:.2f}
    
    Recent price data:
    {data_str}
    
    Based on the above data, provide a trading decision in the following JSON format:
    {{
        "stock": "{symbol}",
        "action": "BUY or SELL or HOLD",
        "reasoning": "Brief explanation for your decision",
        "entry_price": float,
        "stop_loss": float,
        "take_profit": float,
        "order_type": "INTRADAY or DELIVERY",
        "risk_score": integer (1-10, with 10 being highest risk),
        "confidence": integer (1-10, with 10 being highest confidence)
    }}
    
    Ensure your response contains only valid JSON.
    """

    prompt += "\nRespond strictly with JSON format and no additional text."
    return prompt

def get_trade_decision(symbol: str) -> Tuple[Optional[Dict], Optional[str]]:
    _, client, missing_keys = initialize_dhan_and_krutrim()
    if missing_keys:
        return None, f"Missing API keys: {', '.join(missing_keys)}"
    
    prompt = generate_trading_prompt(symbol)
    
    try:
        model_name = "DeepSeek-R1"
        messages = [{"role": "user", "content": prompt}]
        response = client.chat.completions.create(model=model_name, messages=messages)
        
        trade_data = response.choices[0].message.content
        print(trade_data)
        try:
            start_idx = trade_data.find('{')
            end_idx = trade_data.rfind('}') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = trade_data[start_idx:end_idx]
                return json.loads(json_str), None
            return None, "No valid JSON found in AI response"
        except json.JSONDecodeError as e:
            return None, f"Invalid JSON format: {e}"
    except Exception as e:
        return None, f"Error getting trade decision: {e}"

# def execute_trade(trade: Dict) -> Tuple[bool, str]:
#     dhan, _, missing_keys = initialize_dhan_and_krutrim()
#     if missing_keys:
#         return False, f"Missing API keys: {', '.join(missing_keys)}"
    
#     try:
#         stock = trade['stock']
#         action = trade['action'].upper()
        
#         if action == "HOLD":
#             return True, "No trade executed as decision was to HOLD"
        
#         if stock not in SEC_DICT:
#             return False, f"Security ID not found for {stock}"
        
#         response = dhan.place_order(
#             security_id=SEC_DICT[stock],
#             exchange_segment=dhan.NSE,
#             transaction_type=dhan.BUY if action=='BUY' else dhan.SELL,
#             quantity=1,
#             order_type=dhan.MARKET,
#             product_type=dhan.INTRA if trade.get('order_type', 'INTRADAY').upper() == 'INTRADAY' else dhan.CNC,
#             price=0
#         )
#         return True, f"Order placed: {json.dumps(response)}"
#     except Exception as e:
#         return False, f"Error executing trade: {e}"

def execute_trade(trade: Dict) -> Tuple[bool, str]:
    """
    Simulates trade execution for UI feedback without placing a real order.
    """
    try:
        stock = trade['stock']
        action = trade['action'].upper()

        if action == "HOLD":
            return True, "No trade executed as decision was to HOLD"
        simulated_response = {
            "status": "success",
            "message": f"Simulated {action} trade for {stock} logged.",
            "trade_details": {
                "stock": stock,
                "action": action,
                "entry_price": trade.get("entry_price", 0),
                "stop_loss": trade.get("stop_loss", 0),
                "take_profit": trade.get("take_profit", 0),
                "order_type": trade.get("order_type", "INTRADAY"),
                "risk_score": trade.get("risk_score", 1),
                "confidence": trade.get("confidence", 1),
                "timestamp": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }

        st.session_state.trade_history.append(simulated_response["trade_details"])
        return True, json.dumps(simulated_response, indent=2)

    except Exception as e:
        return False, f"Error simulating trade execution: {e}"
