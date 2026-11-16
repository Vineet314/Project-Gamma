from typing import Any
import random

def technical_agent(state: dict[str, Any]) -> dict[str, Any]:
    """
    A mock agent that does technical analysis of a given stock.
    """

    assert state["analysis_type"] in ["technical", "full"], 'Technical agent can only do technical analysis'
    
    ticker = state["stock_symbol"]

    O = random.randint(100,5000)
    H = O*(1 + random.uniform(0,19.9))
    L = O*(1 - random.uniform(0,19.9))
    C = random.uniform(L,H)
    OHLC = [O,H,L,C]
    RSI = random.uniform(10,90)
    MA200 = C*random.uniform(0.75,1.5)
    MA50 = C*random.uniform(0.75,1.5)
    Vol = random.uniform(0.5,100)*1e5


    keys = ['OHLC', 'RSI', 'MA50', 'MA200', 'Volume']
    values = [OHLC,RSI,MA50,MA200,Vol]

    return {'technical_analysis':{
        "status": "completed",
        "data": {i:j for i,j in zip(keys,values)},
        "error":None,
        "attempts":1}} # state update: give list of next agent/s to call